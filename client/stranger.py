import time
from datetime import datetime
import colorsys
import random
from threading import Thread
import sys

import stranger_client

from neopixel import *

LED_COUNT = 50
GPIO_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 5
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0
LED_STRIP = ws.WS2811_STRIP_RGB   # Strip type and colour ordering

record_file = open("/home/pi/Desktop/stranger things/messages.txt", "a+")

CHAR_IDX = {'A': 0, 'B': 2, 'C': 3, 'D': 5, 'E': 7, 'F': 9, 'G': 11, 'H': 13, 'I': 32, 'J': 30, 'K': 28, 'L': 27,
            'M': 25, 'N': 23, 'O': 21, 'P': 19, 'Q': 18, 'R': 36, 'S': 37, 'T': 39, 'U': 40, 'V': 42, 'W': 44, 'X': 46,
            'Y': 48, 'Z': 49, ' ': "NONE", '!': "FLASH", '*': "CREEP"}

strip = Adafruit_NeoPixel(LED_COUNT, GPIO_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
#strip = Adafruit_NeoPixel(LED_COUNT, GPIO_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()
strip.show()


def rand_color():
    return color_of(random.random())


def color_of(i):
    random.seed(i)
    rgb = colorsys.hsv_to_rgb(random.random(), 1, 1)
    return 200, int(rgb[1] * 255), int(rgb[2] * 255)
    #return (0,250,250)


def set_color(led, c):
    strip.setPixelColorRGB(led, c[0], c[1], c[2])


def set_all(color):
    for i in range(0, LED_COUNT):
        set_color(i, color)


def set_all_color_of():
    for i in range(0, LED_COUNT):
        set_color(i, color_of(i))


def creep(n):
    for i in range(0, n):
        set_color((i-1) % LED_COUNT, (0, 0, 0))
        set_color(i % LED_COUNT, rand_color())
        strip.show()
        time.sleep(1)

def clearAll():
    for i in range(0, LED_COUNT):
        set_all((0, 0, 0))

def testAll():
    clearAll()
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
        set_all_color_of()
        strip.show()
        time.sleep(1)
        set_all((0, 0, 0))
        strip.show()
        time.sleep(.5)

displaying = False


def display(msg):
    global displaying
    displaying = True
    for c in msg:
        clearAll()
        if c.upper() in CHAR_IDX:
            i = CHAR_IDX[c.upper()]
            if i == "NONE":
                "do nothing"
            elif i == "FLASH":
                flash(5)
            elif i == "CREEP":
                creep(50)
            else:
                set_color(i, color_of(i))
            strip.show()
            time.sleep(1)
            set_all((0, 0, 0))
            strip.show()
            time.sleep(.2)
    flash(2)
    time.sleep(1)
    displaying = False


def record(msg):
    record_file.write(str(datetime.now())+"\n")
    record_file.write(msg+"\n\n")
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
            set_all((0, 0, 0))
        time.sleep(2)

t0 = Thread(target=listen_on_console, args=("",))
t1 = Thread(target=listen_on_client, args=())
t2 = Thread(target=clear_errors, args=())

#t0.start()
#t1.start()
#t2.start()

display("test test test")
# listen_on_client()
