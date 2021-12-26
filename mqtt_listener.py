import time

import paho.mqtt.client as mqtt
import xml.dom.minidom


def on_connect(client, userdata, flags, rc):
    print('connected with result code ' + str(rc))

    client.subscribe('garage/door_switch/#')
    client.subscribe('wled/c656f8/#')
    client.subscribe('wled/all/#')


def on_message(client, userdate, msg):
    payload = str(msg.payload)
    if msg.topic == 'wled/c656f8/v':
        xml_payload = xml.dom.minidom.parseString(msg.payload)
        payload = xml_payload.toprettyxml()

    print(''.join([str(time.time()), ' ', msg.topic, ' ', payload]))


if __name__ == '__main__':
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.username_pw_set('client1', 'client1')
    client.connect('kellerverwaltung', 9001, 60)

    client.loop_forever()
