import RPi.GPIO
import signal
import paho.mqtt.publish as publish
import sys

request_exit_poll_reed_relay = 0


def sigint_handler(signal_received, frame):
    request_exit_poll_reed_relay = 1
    print('SIGINT or CTRL-C detected. Exiting gracefully')


def send_value(name, value, auth):

    publish.single(
        topic='reed_relay_switch/' + str(name) + '/value',
        payload=str(value),
        auth=auth,
        hostname='kellerverwaltung',
        port=9001
    )


#mqtt setup
auth = {
    'username': 'client2',
    'password': 'client2'
}


def top_switch(channel):
    global auth
    print('top')
    val = RPi.GPIO.input(channel)
    send_value(0, val, auth)


def bottom_switch(channel):
    global auth
    print('bottom')
    val = RPi.GPIO.input(channel)
    send_value(1, val, auth)


def signal_handler(sig, frame):
    RPi.GPIO.cleanup()
    sys.exit(0)


if __name__ == '__main__':
    
    # general setup
    #signal(SIGINT, sigint_handler)

    # gpio setup
    gpio_0 = 11
    gpio_1 = 13
    RPi.GPIO.setmode(RPi.GPIO.BOARD)
    RPi.GPIO.setup(gpio_0, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
    RPi.GPIO.setup(gpio_1, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
    
    RPi.GPIO.add_event_detect(gpio_0, RPi.GPIO.BOTH, callback=top_switch, bouncetime=100)
    RPi.GPIO.add_event_detect(gpio_1, RPi.GPIO.BOTH, callback=bottom_switch, bouncetime=100)
        

    val_old = [RPi.GPIO.input(gpio_0), RPi.GPIO.input(gpio_1)]    
    # publish initial values
    send_value(0, val_old[0], auth)
    send_value(1, val_old[1], auth)
    
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
