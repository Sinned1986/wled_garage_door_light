import threading

import RPi.GPIO
import signal
import paho.mqtt.publish as publish
import sys
from functools import partial
import asyncio

request_exit_poll_reed_relay = 0


def sigint_handler(signal_received, frame):
    request_exit_poll_reed_relay = 1
    print('SIGINT or CTRL-C detected. Exiting gracefully')


def send_value(name, value, auth):

    publish.single(
        topic=''.join(['garage/door_switch/', name, '/value']),
        payload=str(value),
        auth=auth,
        hostname='kellerverwaltung',
        port=9001
    )


class ValueCache:
    def __init__(self):
        self.mutex = threading.Lock()
        self.values = {}


async def check_switch_again(channel_names, asyncio_loop, bounce_time, auth, value_cache, channel):
    await asyncio.sleep(bounce_time)
    triggered_switch(channel_names, asyncio_loop, bounce_time, auth, value_cache, channel)


def triggered_switch(channel_names, asyncio_loop, bounce_time, auth, value_cache, channel):
    value_cache.mutex.acquire()
    print(channel)
    new_val = RPi.GPIO.input(channel)
    if value_cache.values[channel] != new_val:
        value_cache.values[channel] = new_val
        send_value(channel_names[channel], new_val, auth)
        asyncio.ensure_future(check_switch_again(channel_names, asyncio_loop, bounce_time, auth, value_cache, channel), loop=asyncio_loop)  # fire and forget
    value_cache.mutex.release()


def signal_handler(sig, frame):
    RPi.GPIO.cleanup()
    sys.exit(0)


def main(asyncio_loop):
    # general setup
    #signal(SIGINT, sigint_handler)

    # mqtt setup
    auth = {
        'username': 'client2',
        'password': 'client2'
    }

    value_cache = ValueCache()

    # gpio setup
    gpio_0 = 11
    gpio_1 = 13
    channel_names = {
        gpio_0: 'top',
        gpio_1: 'bottom',
    }
    RPi.GPIO.setmode(RPi.GPIO.BOARD)
    RPi.GPIO.setup(gpio_0, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
    RPi.GPIO.setup(gpio_1, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)

    bouncetime = 0.050 # 50 ms in s
    f = partial(triggered_switch, channel_names, asyncio_loop, bouncetime, auth, value_cache)
    RPi.GPIO.add_event_detect(gpio_0, RPi.GPIO.BOTH, callback=f, bouncetime=int(bouncetime*1000))
    RPi.GPIO.add_event_detect(gpio_1, RPi.GPIO.BOTH, callback=f, bouncetime=int(bouncetime*1000))

    val_old = [RPi.GPIO.input(gpio_0), RPi.GPIO.input(gpio_1)]

    # publish initial values
    value_cache.mutex.acquire()
    value_cache.values[gpio_0] = val_old[0]
    value_cache.values[gpio_1] = val_old[1]
    send_value(channel_names[gpio_0], val_old[0], auth)
    send_value(channel_names[gpio_1], val_old[1], auth)
    value_cache.mutex.release()


    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()


    #print(val_old)
    #while request_exit_poll_reed_relay == 0:
    #    val_new = [RPi.GPIO.input(11), RPi.GPIO.input(13)]
    #    if  val_new != val_old:
    #        print(val_new)
    #        val_old = val_new
    #        RPi.GPIO.input(11)
    #        send_value(1, val_old[1], auth)
    #    if request_exit_poll_reed_relay == 1:
    #        exit(0)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))

    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))

