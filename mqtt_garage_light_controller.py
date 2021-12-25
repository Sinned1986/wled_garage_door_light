import time

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import xml.dom.minidom
import xmltodict
import json
import wled_config
from functools import partial


def _on_connect(client, userdata, flags, rc):
    print('connected with result code ' + str(rc))

    client.subscribe('wled/c656f8/#')
    client.subscribe('wled/all/#')
    client.subscribe('garage/door_switch/#')


class GarageLightController:
    switch0 = 1
    switch1 = 1

    def __init__(self, mqtt_auth):
        self._auth = mqtt_auth

        client = mqtt.Client()
        client.on_connect = _on_connect
        client.on_message = self._on_message

        client.username_pw_set('client1', 'client1')
        client.connect('kellerverwaltung', 9001, 60)
        self._client = client
        self._switches = {
            'top': -1,
            'bottom': -1,
        }
        self._run_sequence('init')

    def _send(self, payload):
        self._client.publish(
            topic='wled/all/api',
            payload=payload
        )

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
        if name == 'close':
            self._send(json.dumps(wled_config.wled_pattern_json['off']))
            time.sleep(0.75)
            self._send(json.dumps(wled_config.wled_pattern_json['green']))
            time.sleep(5)
            self._send(json.dumps(wled_config.wled_pattern_json['white']))
            time.sleep(2.25)
            self._send(json.dumps(wled_config.wled_pattern_json['off']))
            time.sleep(0.75)
            self._send(json.dumps(wled_config.wled_pattern_json['spot']))
            time.sleep(2)
            self._send(json.dumps(wled_config.wled_pattern_json['dim']))
        elif name == 'open':
            self._send(json.dumps(wled_config.wled_pattern_json['off']))
            time.sleep(0.75)
            self._send(json.dumps(wled_config.wled_pattern_json['red']))
            time.sleep(0.75)
        elif name == 'init':
            self._send(json.dumps(wled_config.wled_pattern_json['off']))
            time.sleep(0.75)
            self._send(json.dumps(wled_config.wled_pattern_json['white']))
            time.sleep(2.25)
            self._send(json.dumps(wled_config.wled_pattern_json['off']))
            time.sleep(0.75)
            self._send(json.dumps(wled_config.wled_pattern_json['spot']))
            time.sleep(2)
            self._send(json.dumps(wled_config.wled_pattern_json['dim']))
        else:
            raise Exception('unknown sequence')

    def loop_forever(self):
        self._client.loop_forever()


if __name__ == '__main__':
    auth = {
        'username': 'client1',
        'password': 'client1'
    }
    controller = GarageLightController(auth)
    controller.loop_forever()
