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
        self.started = False
        self.playlist = []
        self.playlist_lenght = self.settings["playlist_length"]
        self.buff_size = 65536 # linux pipe buffer size
        self.paused = False

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

    def append_next_item(self):
        next_item = self.get_next_item()
        if not next_item:
            time.sleep(.1)
            return  
        next_item.open(self)
        if next_item:
            logging.debug("Appending {} to playlist".format(next_item))
            self.playlist.append(next_item)
            return 
        logging.error("Unable to get next item")
    

    def start(self):
        self.started = True
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

    def main_thread(self):
        while self.should_run:
            if not self.playlist:
                time.sleep(.01)
                continue
            logging.info("Starting clip {}".format(self.playlist[0]))
            while self.should_run:
                if self.paused:
                    time.sleep(.01)
                    continue
                data = self.current.read(self.buff_size)
                if not data:
                    break
                self.encoder.write(data)
            self.playlist.pop(0)

    def monitor_thread(self):
        while self.should_run:
            while len(self.playlist) < self.playlist_lenght:
                self.append_next_item()
            time.sleep(.1)

    def progress_thread(self):
        sbuff = b""
        ebuff = b""
        while self.should_run:
            if not self.playlist:
                time.sleep(.01)
                continue

            source = self.current
            if source and source.proc.stderr:
                try:
                    ch = source.proc.stderr.read(1)
                except Exception:
                    log_traceback()
                else:
                    if ch in ["\n", "\r", b"\n", b"\r"]:
                        line = decode_if_py3(sbuff)
                        if line.startswith("frame="):
                            m = re.match(r".*frame=\s*(\d+)\s*fps.*", line)
                            if m:
                                current_frame = int(m.group(1))
                                source.position = current_frame / source.meta["video/fps_f"]
                                self.progress_handler()
                        elif CONTI_DEBUG["source"]:
                            logging.debug("SOURCE:", line)
                        sbuff = b""
                    else:
                        sbuff += ch

            continue # TODO: move to another thread??
            if self.encoder and self.encoder.proc.stderr: 
                try:
                    ch = self.encoder.proc.stderr.read(1)
                except Exception:
                    log_traceback()
                else:
                    if ch in ["\n", "\r", b"\n", b"\r"]:
                        line = decode_if_py3(ebuff)
                        #TODO: get fps/speed value to track performance
                        ebuff = b""
                    else:
                        ebuff += ch


    def progress_handler(self):
        return
        print (self.current.base_name, self.current.position)

    def stop(self):
        logging.warning("You should never stop your channel :)")
        self.should_run = False
        self.encoder.stop()
        self.take()

    #
    # Playback interaction
    #

    def take(self):
        """Finish current item and skip to next one"""
        if not self.playlist:
            logging.error("Unable to take. Playlist is empty.")
            return False
        current = self.current
        if not current:
            logging.error("Unable to take. No clip is playing")
            return False
        current.stop()
        return True

    # WARNING:  Freeze and abort should not be used if output is IP stream!
    # TODO: disallow this by checking output formats

    def freeze(self):
        self.paused = not self.paused

    def retake(self):
        logging.error("Retake is not implemented")
        return False

    def abort(self):
        logging.info("Aborting", self.current)
        self.current.stop()
        self.paused = True

