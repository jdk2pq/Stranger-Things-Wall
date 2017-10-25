import random
import sys
import time
from datetime import datetime
from threading import Thread

from neopixel import *

import stranger_client

LED_COUNT = 50
GPIO_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 5
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0
LED_STRIP = ws.WS2811_STRIP_RGB  # Strip type and colour ordering

displaying = False

record_file = open("/home/pi/Desktop/stranger things/messages.txt", "a+")

CHAR_IDX = {
    'A': 48,
    'B': 47,
    'C': 45,
    'D': 43,
    'E': 42,
    'F': 40,
    'G': 39,
    'H': 37,
    'I': 20,
    'J': 22,
    'K': 24,
    'L': 25,
    'M': 26,
    'N': 27,
    'O': 29,
    'P': 31,
    'Q': 33,
    'R': 14,
    'S': 13,
    'T': 12,
    'U': 10,
    'V': 9,
    'W': 7,
    'X': 5,
    'Y': 3,
    'Z': 1,
    ' ': "NONE",
    '!': "FLASH",
    '*': "CREEP"
}

strip = Adafruit_NeoPixel(LED_COUNT, GPIO_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
strip.begin()
strip.show()


def rand_color():
    return get_new_color(random.random(), False)


def get_new_color(i, include_blue):
    random.seed(i)
    # blue channel doesn't work well with my lights when lighting up a single LED
    if include_blue:
        return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    else:
        return 0, random.randint(0, 255), random.randint(0, 255)


def set_color(led, c):
    strip.setPixelColorRGB(led, c[0], c[1], c[2])


def set_all(color):
    for i in range(0, LED_COUNT):
        set_color(i, color)


def set_all_new_color():
    for i in range(0, LED_COUNT):
        set_color(i, get_new_color(i, True))


def creep(n):
    for i in range(0, n):
        set_color((i - 1) % LED_COUNT, (0, 0, 0))
        set_color(i % LED_COUNT, rand_color())
        strip.show()
        time.sleep(1)


def build():
    clear_all()
    strip.show()
    for i in range(0, LED_COUNT):
        set_color(i, rand_color())
        strip.show()
        time.sleep(.3)
    flash(2)


def clear_all():
    for i in range(0, LED_COUNT):
        set_all((0, 0, 0))


def test_all():
    clear_all()
    for i in range(0, 50):
        print("setting color for {}".format(i))
        set_color(i, (0, 0, 0))
        time.sleep(1)
        set_color(i, (255, 0, 0))
        strip.show()
        time.sleep(2)
        set_color(i, (0, 0, 0))


def flash(n):
    for i in range(0, n):
        set_all_new_color()
        strip.show()
        time.sleep(1)
        clear_all()
        strip.show()
        time.sleep(.5)


def display(msg):
    global displaying
    displaying = True
    for c in msg:
        clear_all()
        if c.upper() in CHAR_IDX:
            i = CHAR_IDX[c.upper()]
            if i == "NONE":
                "do nothing"
            elif i == "FLASH":
                flash(3)
            elif i == "CREEP":
                creep(50)
            else:
                set_color(i, get_new_color(i, False))
            strip.show()
            time.sleep(1)
            clear_all()
            strip.show()
            time.sleep(.2)
    time.sleep(1)
    displaying = False


def record(msg):
    record_file.write(str(datetime.now()) + "\n")
    record_file.write(msg + "\n\n")
    record_file.flush()


def listen_on_console(prompt):
    while True:
        try:
            msg = raw_input(prompt)
            display(msg)
        except KeyboardInterrupt:
            sys.exit()


def listen_on_client():
    global displaying
    while True:
        if not displaying:
            try:
                msgs = stranger_client.get_messages()
                for msg in msgs:
                    print msg
                    record(msg)
                    display(msg[:50])
            except:
                print "network error"
        time.sleep(2)


def clear_errors():
    global displaying
    while True:
        if not displaying:
            clear_all()
        time.sleep(2)


t0 = Thread(target=listen_on_console, args=("",))
t1 = Thread(target=listen_on_client, args=())
t2 = Thread(target=clear_errors, args=())

t0.start()
# t1.start()
# t2.start()

display("test test test")
# listen_on_client()
