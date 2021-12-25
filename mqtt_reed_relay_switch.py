import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import xml.dom.minidom
import xmltodict
import json

switch0 = 1
switch1 = 1

def on_connect(client, userdata, flags, rc):
    print('connected with result code ' + str(rc))

    client.subscribe('wled/c49bb0/#')
    client.subscribe('wled/all/#')
    client.subscribe('reed_relay_switch/#')

def on_message(client, userdate, msg):
    global switch0
    global switch1
    updateWLED = 0

    payload = str(msg.payload)
    if msg.topic == 'wled/c49bb0/v':
        payload_xml  = xml.dom.minidom.parseString(msg.payload)
        
        payload_dict = xmltodict.parse(msg.payload)
        payload = payload_xml.toprettyxml() + json.dumps(payload_dict, indent = 2)

    if msg.topic == 'reed_relay_switch/0/value':
        if (switch0 != int(msg.payload)):
            updateWLED = 1
            switch0 = int(msg.payload)
    if msg.topic == 'reed_relay_switch/1/value':
        if (switch1 != int(msg.payload)):
            updateWLED = 1
            switch1 = int(msg.payload)

    auth = {
        'username' : 'client1',
        'password' : 'client1'
    }

    if updateWLED == 1:
        if switch0 == 0:
            publish.single(
                topic='wled/all/api',
                payload='win&FX=0&CL=#00FF00', 
                auth=auth,
                hostname='kellerverwaltung',
                port=9001
            )
        elif switch1 == 0:
            publish.single(
                topic='wled/all/api',
                payload='win&FX=0&CL=#FF0000', 
                auth=auth,
                hostname='kellerverwaltung',
                port=9001
            )
        else:
            publish.single(
                topic='wled/all/api',
                payload='win&FX=38&CL=#FFA000' , 
                auth=auth,
                hostname='kellerverwaltung',
                port=9001
            )
        
    

    print(msg.topic + ' ' + payload)


if __name__ == '__main__':
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    

    client.username_pw_set('client1', 'client1')
    client.connect('kellerverwaltung', 9001, 60)



    client.loop_forever()  