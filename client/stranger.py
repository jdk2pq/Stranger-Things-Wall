import random
import sys
import time
from datetime import datetime
from threading import Thread

from neopixel import *
import argparse
import csv
import fcntl
import logging
import os
import signal
import sys
import time

from BeautifulSoup import BeautifulSoup
from googlevoice import Voice
from googlevoice.util import LoginError, ValidationError
from threading import Thread

import stranger_client

class Sms(Thread):
    """Check SMS messages from a Google Voice account to control the lightshow

    When executed, this script will check all the SMS messages from a Google Voice account checking
    for either the "help" command, which will cause a help message to be sent back to the original
    sender, or a single number indicating which song they are voting for.

    When a song is voted for, the playlist file will be updated with the sender's cell phone number
    to indicate it has received a vote from that caller.  This also enforces only a single vote per
    phone number per s (until that song is played).

    See the commands.py file for other commands that are also supported (as well as instructions on
    adding new own commands).

    Sample usage:

    sudo python check_sms.py --playlist=/home/pi/music/.playlist

    For initial setup:

    sudo python check_sms.py --setup=True

    Third party dependencies:

    pygooglevoice: http://sphinxdoc.github.io/pygooglevoice/
    Beautiful Soup: http://www.crummy.com/software/BeautifulSoup/
    """

    def __init__(self, setup=False):
        super(Sms, self).__init__()
        self.daemon = True
        self.cancelled = False

        if setup:
            self.cancelled = True

        levels = {'DEBUG': logging.DEBUG,
                  'INFO': logging.INFO,
                  'WARNING': logging.WARNING,
                  'ERROR': logging.ERROR,
                  'CRITICAL': logging.CRITICAL}

        level = logging.DEBUG
        logging.basicConfig()
        logging.getLogger().setLevel(level)
        self.voice = Voice()

    def run(self):
        """Overloaded Thread.run, runs the update
        method once per every 5 seconds."""
        self.login()

        while not self.cancelled:
            try:
                self.update()
            except:
                logging.error(
                    'Error when checking for sms messages, will try again in 5 seconds.',
                    exc_info=1)

            time.sleep(5)

    def cancel(self):
        """End this timer thread"""
        self.cancelled = True

    def update(self):
        """Check for new messages"""
        self.check()

    def login(self):
        """Login to google voice account

        Setup your username and password in ~/.gvoice (or /root/.gvoice when running as root)
        file as follows to avoid being asked for your email and password each time:

        [auth]
        email=<google voice email address>
        password=<google voice password>
        """

        # make sure we are logged in
        # if unable to login wait 30 seconds and try again
        # if unable to login after 3 attempts exit check_sms
        logged_in = False
        attempts = 0
        while not logged_in:
            try:
                self.voice.login()
                logged_in = True
                logging.info("Successfully logged in to Google Voice account")
            except LoginError as error:
                attempts += 1
                if attempts <= 3:
                    time.sleep(30)
                else:
                    logging.critical('Unable to login to Google Voice, Exiting SMS.')
                    self.cancelled = True
                    sys.exit()

    @staticmethod
    def extract_sms(html_sms):
        """Extract SMS messages from BeautifulSoup tree of Google Voice SMS Html,

        returning a list of dictionaries, one per message.

        extract_sms - taken from http://sphinxdoc.github.io/pygooglevoice/examples.html
        originally written by John Nagle (nagle@animats.com)

        :param html_sms: Google Voice SMS Html data
        :type html_sms: BeautifulSoup object

        :return: msg_items
        :rtype: dictionary
        """
        msgitems = []

        # parse HTML into tree
        tree = BeautifulSoup(html_sms)
        conversations = tree.findAll("div", attrs={"id": True}, recursive=False)

        for conversation in conversations:
            # For each conversation, extract each row, which is one SMS message.
            rows = conversation.findAll(attrs={"class": "gc-message-sms-row"})
            # for all rows
            for row in rows:

                # For each row, which is one message, extract all the fields.
                # tag this message with conversation ID
                msgitem = {"id": conversation["id"]}
                spans = row.findAll("span", attrs={"class": True}, recursive=False)

                # for all spans in row
                for span in spans:
                    name = span['class'].replace('gc-message-sms-', '')

                    # put text in dict
                    msgitem[name] = (" ".join(span.findAll(text=True))).strip()

                # add msg dictionary to list
                msgitems.append(msgitem)

        return msgitems


    def check(self):
        """Process sms messages

        Download and process all sms messages from a Google Voice account.
        this is executed every 5 seconds
        """

        # Parse and act on any new sms messages
        messages = self.voice.sms().messages
        for msg in self.extract_sms(self.voice.sms.html):
            logging.debug(str(msg))
            self.voice.send_sms(msg['from'], 'Sent to the upside down')
            print msg
            while displaying:
                time.sleep(5)
            record(msg['text'])
            display(msg['text'])

        # Delete all messages now that we've processed them
        for msg in messages:
            msg.delete(1)

LED_COUNT = 50
GPIO_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 5
LED_BRIGHTNESS = 15
LED_INVERT = False
LED_CHANNEL = 0
LED_STRIP = ws.WS2811_STRIP_RGB  # Strip type and colour ordering

displaying = False
build_iter = 1

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
    '*': "CREEP",
    '@': "ALPHABET"
}

strip = Adafruit_NeoPixel(LED_COUNT, GPIO_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
strip.begin()
strip.show()


def rand_color():
    return get_new_color(random.random())


def get_new_color(i):
    random.seed(i)
    rand = random.randint(0, 6)
    if rand == 0:
        return 0, 0, 255
    elif rand == 1:
        return 0, 255, 255
    elif rand == 2:
        return 0, 255, 0
    elif rand == 3:
        return 255, 255, 0
    elif rand == 4:
        return 255, 0, 0
    elif rand == 5:
        return 255, 0, 255
    else:
        return 255, 255, 255


def set_color(led, c):
    strip.setPixelColorRGB(led + 1, c[0], 0, 0)
    strip.setPixelColorRGB(led, 0, c[1], c[2])


def set_all(color):
    for i in range(0, LED_COUNT):
        set_color(i, color)


def set_all_new_color():
    for i in range(0, LED_COUNT):
        set_color(i, get_new_color(i))


def creep(n):
    for i in range(0, n):
        set_color((i - 1) % LED_COUNT, (0, 0, 0))
        set_color(i % LED_COUNT, rand_color())
        strip.show()
        time.sleep(1)


def build():
    global build_iter
    clear_all()
    strip.show()
    if build_iter % 2 == 0:
        num_list = range(LED_COUNT, -1, -1)
    else:
        num_list = range(0, LED_COUNT)
    for i in num_list:
        if displaying:
            break
        else:
            new_color = rand_color()
            strip.setPixelColorRGB(i, new_color[0], new_color[1], new_color[2])
            strip.show()
            time.sleep(.3)
    build_iter += 1


def clear_all():
    set_all((0, 0, 0))
    strip.show()


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
    time.sleep(1)
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
            elif i == "ALPHABET":
                alphabet()
            else:
                set_color(i, get_new_color(i))
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
            build()
        time.sleep(2)


# borrowed from https://github.com/jgarff/rpi_ws281x/blob/master/python/examples/strandtest.py
def color_wipe(color, wait_ms=800):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def alphabet():
    display("abcdefghijklmnopqrstuvwxyz")


console_thread = Thread(target=listen_on_console, args=("",))
clear_errors_thread = Thread(target=clear_errors, args=())
check_sms_thread = Sms

console_thread.start()
clear_errors_thread.start()
check_sms_thread.start()
