import json

import paho.mqtt.publish as publish
import time


import wled_config


class Controller:

    def __init__(self):
        self.auth = {
            'username': 'client2',
            'password': 'client2'
        }

    def send(self, light_mode):
        #for pattern in self.wled_pattern_http_api[light_mode]:
        pattern = json.dumps(light_mode)
        publish.single(
            topic='wled/all/api',
            payload=pattern,
            auth=self.auth,
            hostname='kellerverwaltung',
            port=9001
        )


if __name__ == '__main__':

    controller = Controller()
    light_modes = [
        ['off', 1],
        ['white', 2.25],
        ['off', 0.75],
        ['spot', 5],
        ['off', 0.75],
        ['red', 8],
        ['off', 0.75],
        ['green', 5],
        ['white', 2.25],
        ['off', 0.75],
        ['spot', 2],
        ['dim', 0],
    ]
    for light_mode, duration in light_modes:
        print('send %s' % light_mode)
        controller.send(wled_config.wled_pattern_json[light_mode])
        time.sleep(duration)


