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
        topic='garage/door_switch/' + str(name) + '/value',
        payload=str(value),
        auth=auth,
        hostname='kellerverwaltung',
        port=9001
    )


class ValueCache:
    def __init__(self):
        self.mutex = threading.Lock()
        self.values = {}


async def check_switch_again(bounce_time, auth, value_cache, channel):
    await asyncio.sleep(bounce_time)
    triggered_switch(bounce_time, auth, value_cache, channel)


def triggered_switch(bounce_time, auth, value_cache, channel):
    value_cache.mutex.aquire()
    print(channel)
    new_val = RPi.GPIO.input(channel)
    if value_cache.values[channel] != new_val:
        value_cache.values[channel] = new_val
        send_value(channel, new_val, auth)
        asyncio.ensure_future(check_switch_again(bounce_time, auth, value_cache, channel))  # fire and forget
    value_cache.mutex.release()


def signal_handler(sig, frame):
    RPi.GPIO.cleanup()
    sys.exit(0)


def main():
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
    RPi.GPIO.setmode(RPi.GPIO.BOARD)
    RPi.GPIO.setup(gpio_0, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
    RPi.GPIO.setup(gpio_1, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)

    bouncetime = 0.050 # 50 ms in s
    f_isr = partial(triggered_switch, bouncetime*1.1, auth, value_cache) # increase delay to be sure to miss no transition
    f0 = partial(triggered_switch, bouncetime, auth, value_cache, 0)
    f1 = partial(triggered_switch, bouncetime, auth, value_cache, 1)
    RPi.GPIO.add_event_detect(gpio_0, RPi.GPIO.BOTH, callback=f0, bouncetime=int(bouncetime*1000))
    RPi.GPIO.add_event_detect(gpio_1, RPi.GPIO.BOTH, callback=f1, bouncetime=int(bouncetime*1000))

    val_old = [RPi.GPIO.input(gpio_0), RPi.GPIO.input(gpio_1)]

    # publish initial values
    value_cache.mutex.acquire()
    value_cache.values[0] = val_old[0]
    value_cache.values[1] = val_old[1]
    send_value(0, val_old[0], auth)
    send_value(1, val_old[1], auth)
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
    loop.run_until_complete(main())

    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))

