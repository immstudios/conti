import os
import re
import sys
import time
import subprocess

from .common import *
from .encoder import ContiEncoder
from .source import ContiSource

__all__ = ["Conti", "ContiSource", "CONTI_DEBUG"]


class Conti(object):
    def __init__(self, get_next_item, **kwargs):
        self.get_next_item = get_next_item
        self.settings = get_settings(**kwargs)

        self.playlist = []
        self.playlist_lenght = 3
        self.buff_size = 4*1024*1024

        self.encoder = ContiEncoder(self)

    @property
    def current(self):
        if not self.playlist:
            return False
        return self.playlist[0]

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
            if not next_item:
                time.sleep(.1)
                continue
            next_item.open(self)
            if next_item:
                logging.debug("Appending {} to playlist".format(next_item))
                self.playlist.append(next_item)
                continue
            logging.error("Unable to get next item")


    def start(self):
        self.encoder.start()
        thread.start_new_thread(self.monitor_thread, ())
        thread.start_new_thread(self.progress_thread, ())
        while not self.playlist:
            logging.debug("Playlist is not ready")
            time.sleep(.1)
        if self.settings.get("blocking", True):
            logging.debug("Starting main thread in blocking mode")
            self.main_thread()
        else:
            logging.debug("Starting main thread in non-blocking mode")
            thread.start_new_thread(self.main_thread, ())


    def stop(self):
        logging.warning("You should never stop your broadcasting :)")


    def main_thread(self):
        while True:
            logging.info("Starting clip {}".format(self.playlist[0]))
            while True:
                data = self.current.read(self.buff_size)
                if not data:
                    break
                self.encoder.write(data)
            self.playlist.pop(0)

    def monitor_thread(self):
        while True:
            self.fill_playlist()
            time.sleep(.1)

    def progress_thread(self):
        buff = ""
        while True:
            if not self.playlist:
                time.sleep(.01)
                continue

            source = self.current
            if not (source or source.stderr):
                time.sleep(.01)
                continue

            try:
                ch = decode_if_py3(source.proc.stderr.read(1))
            except Exception:
                log_traceback()
                continue

            if ch in ["\n", "\r"]:
                if buff.startswith("frame="):
                    m = re.match(r".*frame=\s*(\d+)\s*fps.*", buff)
                    if m:
                        current_frame = int(m.group(1))
                        source.position = current_frame / source.meta["video/fps_f"]
                        self.progress_handler()
                buff = ""
            else:
                buff += ch


    def progress_handler(self):
        return
        print (self.current.base_name, self.current.position)
