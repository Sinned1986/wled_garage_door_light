import threading
import time
import paho.mqtt.client as mqtt
import xml.dom.minidom
import xmltodict
import json
import wled_config
import signal

def _on_connect(client, userdata, flags, rc):
    print('connected with result code ' + str(rc))

    client.subscribe('wled/c656f8/#')
    client.subscribe('wled/all/#')
    client.subscribe('garage/door_switch/#')


class CmdQueueSyncException(Exception):
    pass


# we need a threadsafe clearable queue for led commands, insert tuple of [duration in ms as int, json-string]
class CmdQueue:
    def __init__(self):
        self.cmd_queue = []
        self.cmd_queue_mutex = threading.Lock()
        self.cmd_event = threading.Event()

    def queue(self, value):
        self.cmd_queue_mutex.acquire()
        try:
            self.cmd_queue.append(value)
            self.cmd_event.set()
        finally:
            self.cmd_queue_mutex.release()

    def dequeue(self):
        while not self.cmd_event.is_set():
            self.cmd_event.wait()
        self.cmd_queue_mutex.acquire()
        try:
            size = len(self.cmd_queue)
            if size == 0:
                raise CmdQueueSyncException()
            if size == 1:
                self.cmd_event.clear()
            return self.cmd_queue.pop(0)
        finally:
            self.cmd_queue_mutex.release()

    def clear(self):
        self.cmd_queue_mutex.acquire()
        try:
            self.cmd_queue.clear()
            self.cmd_event.clear()
        finally:
            self.cmd_queue_mutex.release()

    def unblock(self):
        self.clear()
        self.cmd_event.set()


class GarageLightController:
    switch0 = 1
    switch1 = 1

    def __init__(self):
        self._cmd_queue = CmdQueue()

        mqtt_clients = []
        mqtt_client_loops = []
        with open('config.json') as file:
            config = json.load(file)

        for i in range(2):
            client_name = ''.join(['garage_door_light_controller_', str(i)])
            client = mqtt.Client(client_name)
            client.username_pw_set(client_name, config['client'][client_name])
            mqtt_clients.append(client)

        # mqtt client to subscribe the door sensors
        mqtt_clients[0].on_connect = _on_connect
        mqtt_clients[0].on_message = self._on_message
        self._client_listener = mqtt_clients[0]
        # mqtt client to send cmds to the led controller
        self._client_sender = mqtt_clients[1]

        for client in mqtt_clients:
            client.connect('localhost', 1883, 60)
            mqtt_client_loop = threading.Thread(target=client.loop_forever)
            mqtt_client_loop.start()
            mqtt_client_loops.append(mqtt_client_loop)

        self._mqtt_clients = mqtt_clients
        self._mqtt_client_loops = mqtt_client_loops
        # init internal cache for door sensors
        self._switches = {
            'top': -1,
            'bottom': -1,
        }

        # start the thread which will send cmds to the led controller
        self._run_shutdown_event = threading.Event()
        self._run_interrupt_event = threading.Event()
        self._run_sequence('init')
        self._run = threading.Thread(target=self._sender_thread)
        self._run.start()

    def __del__(self):
        self._run_shutdown_event.set()
        self._cmd_queue.unblock()
        self._run.join()

        for client in self._mqtt_clients:
            client.disconnect()
        for client_loop in self._mqtt_client_loops:
            client_loop.join()

    def _send(self, payload):
        self._client_sender.publish(
            topic='wled/all/api',
            payload=payload
        )

    def _sender_thread(self):
        while not self._run_shutdown_event.is_set():
            try:
                queue_entry = self._cmd_queue.dequeue()
                duration = queue_entry[0]
                json_str = queue_entry[1]
                self._send(json_str)
                _ = self._run_interrupt_event.wait(timeout=duration)  # we don't care if the timeout or the event occured
                self._run_interrupt_event.clear()
            except CmdQueueSyncException:
                pass

    def _on_message(self, client, userdata, msg):
        updateWLED = 0
        payload = str(msg.payload)
        if msg.topic == 'wled/c656f8/v':
            payload_xml = xml.dom.minidom.parseString(msg.payload)

            payload_dict = xmltodict.parse(msg.payload)
            payload = payload_xml.toprettyxml() + json.dumps(payload_dict, indent=2)

        if msg.topic == 'garage/door_switch/top/value':
            if self._switches['top'] != int(msg.payload):
                updateWLED = 1
                self._switches['top'] = int(msg.payload)
        if msg.topic == 'garage/door_switch/bottom/value':
            if self._switches['bottom'] != int(msg.payload):
                updateWLED = 1
                self._switches['bottom'] = int(msg.payload)

        if updateWLED == 1:
            print(''.join(['switches', str(self._switches)]))
            if self._switches['top'] != 0 and self._switches['bottom'] != 0:
                self._run_sequence('open')
            else:
                self._run_sequence('close')

        #print(msg.topic + ' ' + payload)

    def _run_sequence(self, name):
        self._cmd_queue.clear()
        print(''.join(['sequence ', name]))
        if name == 'close':
            self._cmd_queue.queue([0.75, json.dumps(wled_config.wled_pattern_json['off'])])
            self._cmd_queue.queue([5, json.dumps(wled_config.wled_pattern_json['green'])])
            self._cmd_queue.queue([2.250, json.dumps(wled_config.wled_pattern_json['white'])])
            self._cmd_queue.queue([0.75, json.dumps(wled_config.wled_pattern_json['off'])])
            self._cmd_queue.queue([2, json.dumps(wled_config.wled_pattern_json['spot'])])
            self._cmd_queue.queue([0, json.dumps(wled_config.wled_pattern_json['dim'])])
        elif name == 'open':
            self._cmd_queue.queue([0.75, json.dumps(wled_config.wled_pattern_json['off'])])
            self._cmd_queue.queue([0.75, json.dumps(wled_config.wled_pattern_json['red'])])
        elif name == 'init':
            self._cmd_queue.queue([0.75, json.dumps(wled_config.wled_pattern_json['off'])])
            self._cmd_queue.queue([2.250, json.dumps(wled_config.wled_pattern_json['white'])])
            self._cmd_queue.queue([0.75, json.dumps(wled_config.wled_pattern_json['off'])])
            self._cmd_queue.queue([2, json.dumps(wled_config.wled_pattern_json['spot'])])
            self._cmd_queue.queue([0, json.dumps(wled_config.wled_pattern_json['dim'])])
        else:
            raise Exception('unknown sequence')


class QuitGarageLightController:

    def __init__(self):
        self._event = threading.Event()
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def __del__(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

    def signal_handler(self, signum, frame):
        if signum == signal.SIGINT:
            self._event.set()
        if signum == signal.SIGTERM:
            self._event.set()

    def is_set(self):
        return self._event.is_set()

    def wait(self):
        return self._event.wait()


if __name__ == '__main__':

    controller = GarageLightController()
    quit_controller = QuitGarageLightController()
    while not quit_controller.is_set():
        quit_controller.wait()
