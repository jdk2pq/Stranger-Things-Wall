#!/usr/bin/env python
#
# Licensed under the BSD license.  See full license in LICENSE file.
# http://www.lightshowpi.org/
#
# Author: Todd Giles (todd@lightshowpi.org)
#
# Modifications by: Chris Usey (chris.usey@gmail.com)
# Modifications by: Tom Enos (tomslick.ca@gmail.com)
# Modifications by: Jake Kenneally (jakekenneally@gmail.com)


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
import stranger


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
            while stranger.displaying:
                time.sleep(5)
            stranger.record(msg['text'])
            stranger.display(msg['text'])

        # Delete all messages now that we've processed them
        for msg in messages:
            msg.delete(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', default=False,
                        help='use this option to setup the default '
                             'configuration file for Google Voice')
    parser.add_argument('--log', default='INFO',
                        help='Set the logging level. levels:INFO, DEBUG, WARNING, ERROR, CRITICAL')
    args = parser.parse_args()

    check_sms = Sms(args.setup)
    signal.signal(signal.SIGINT, lambda x, y: check_sms.cancel())
    check_sms.start()
    signal.pause()