__all__ = ["Conti", "ContiSource", "CONTI_DEBUG"]


import os
import re
import sys
import time
import subprocess
import signal

from .common import *
from .encoder import *
from .source import *


class Conti(object):
    def __init__(self, get_next_item, **kwargs):
        self.get_next_item = get_next_item
        self.settings = get_settings(**kwargs)
        self.should_run = True
        self.playlist = []
        self.playlist_lenght = 2
        self.buff_size = 65536 # linux pipe buffer size

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
        logging.warning("You should never stop your channel :)")
        self.should_run = False
        self.encoder.stop()
        self.abort()

    def abort(self):
        """Finish current item and skip to next one"""
        if not self.playlist:
            logging.error("Unable to abort current clip. Playlist is empty.")
            return False
        current = self.current
        if not current:
            logging.error("Unable to abort. No clip is playing")
            return False
        current.stop()
        return True

    def main_thread(self):
        while self.should_run:
            logging.info("Starting clip {}".format(self.playlist[0]))
            while self.should_run:
                data = self.current.read(self.buff_size)
                if not data:
                    break
                self.encoder.write(data)
            self.playlist.pop(0)

    def monitor_thread(self):
        while self.should_run:
            self.fill_playlist()
            time.sleep(.1)

    def progress_thread(self):
        buff = b""
        while self.should_run:
            if not self.playlist:
                time.sleep(.01)
                continue

            source = self.current
            if not (source and source.proc.stderr):
                time.sleep(.01)
                continue

            try:
                ch = source.proc.stderr.read(1)
            except Exception:
                log_traceback()
                time.sleep(1)
                continue

            if ch in ["\n", "\r", b"\n", b"\r"]:
                line = decode_if_py3(buff)
                if CONTI_DEBUG["source"]:
                    print (line)
                if line.startswith("frame="):
                    m = re.match(r".*frame=\s*(\d+)\s*fps.*", line)
                    if m:
                        current_frame = int(m.group(1))
                        source.position = current_frame / source.meta["video/fps_f"]
                        self.progress_handler()
                buff = b""
            else:
                buff += ch


    def progress_handler(self):
        return
        print (self.current.base_name, self.current.position)
