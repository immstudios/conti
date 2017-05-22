import os
import sys
import time
import subprocess

from .common import *
from .encoder import ContiEncoder
from .source import ContiSource

__all__ = ["Conti", "ContiSource"]


class Conti(object):
    def __init__(self, get_next_item, **kwargs):
        self.get_next_item = get_next_item
        self.settings = get_settings(**kwargs)

        self.playlist = []
        self.playlist_lenght = 4
        self.buff_size = 1024*1024

        self.encoder = ContiEncoder(self)

    @property
    def vfilters(self):
        return self.encoder.vfilters

    @property
    def afilters(self):
        return self.encoder.afilters

    def fill_playlist(self):
        while len(self.playlist) < self.playlist_lenght:
            logging.debug("Fill playlist!")
            next_item = self.get_next_item()
            next_item.open()
            if next_item:
                logging.debug("Appending {} to playlist".format(next_item))
                self.playlist.append(next_item)
                continue
            logging.error("Unable to get next item")


    def start(self):
        self.encoder.start()
        thread.start_new_thread(self.monitor_thread, ())
        while not self.playlist:
            time.sleep(.1)
        self.main_thread()


    def stop(self):
        logging.warning("You should never stop your broadcasting :)")


    def main_thread(self):
        while True:
            logging.info("Starting clip {}".format(self.playlist[0]))
            while True:
                data = self.playlist[0].read(self.buff_size)
                if not data:
                    break
                self.encoder.write(data)
            self.playlist.pop(0)


    def monitor_thread(self):
        while True:
            self.fill_playlist()
            time.sleep(.1)
