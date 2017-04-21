import os
import time
import subprocess

from .common import *
from .encoder import ContiEncoder
from .source import ContiSource

__all__ = ["Conti", "ContiSource"]


class Conti(object):
    def __init__(self, get_next_item, target, **kwargs):
        self.get_next_item = get_next_item
        self.target = target
        self.settings = get_settings(**kwargs)

        self.playlist = []
        self.playlist_lenght = 2
        self.buff_size = 4096
        self.encoder = ContiEncoder(self)

    def fill_playlist(self):
        while len(self.playlist) < self.playlist_lenght:
            next_item = self.get_next_item()
            next_item.open()
            if next_item:
                logging.debug("Appending {} to playlist".format(next_item))
                self.playlist.append(next_item)
                continue
            logging.error("Unable to get next item")

    def start(self):
        self.encoder.start()

        while True:
            self.fill_playlist()
            time.sleep(.4)

            logging.info("Starting clip {}".format(self.playlist[0]))
            while True:
                data = self.playlist[0].read(self.buff_size)
                if not data:
                    break
                self.encoder.write(data)
            self.playlist.pop(0)

