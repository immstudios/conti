__all__ = ["Conti", "ContiSource", "CONTI_DEBUG"]

import re
import time
import threading

from nxtools import logging, log_traceback
from .common import get_settings, CONTI_DEBUG
from .encoder import ContiEncoder
from .source import ContiSource


class Conti(object):
    def __init__(self, get_next_item, **kwargs):
        self.get_next_item = get_next_item
        self.settings = get_settings(**kwargs)
        self.should_run = True
        self.started = False
        self.playlist = []
        self.playlist_lenght = self.settings["playlist_length"]
        self.buff_size = 65536  # linux pipe buffer size
        self.paused = False
        self.encoder = ContiEncoder(self)

    @property
    def current(self):
        if not self.playlist:
            return False
        return self.playlist[0]

    @property
    def filter_chain(self):
        return self.encoder.filter_chain

    def append_next_item(self):
        next_item = self.get_next_item(self)
        if not next_item:
            time.sleep(.1)
            return
        next_item.open()
        if next_item:
            logging.debug("Appending {} to playlist".format(next_item))
            self.playlist.append(next_item)
            return
        logging.error("Unable to get next item")

    def start(self):
        self.started = True
        self.encoder.start()

        monitor_thread = threading.Thread(
            target=self.monitor_thread,
            daemon=True
        )
        source_progress_thread = threading.Thread(
            target=self.source_progress_thread,
            daemon=True
        )
        encoder_progress_thread = threading.Thread(
            target=self.encoder_progress_thread,
            daemon=True
        )

        monitor_thread.start()
        source_progress_thread.start()
        encoder_progress_thread.start()

        while not self.playlist:
            logging.debug("Playlist is not ready")
            time.sleep(.1)
        if self.settings.get("blocking", True):
            logging.debug("Starting main thread in blocking mode")
            self.main_thread()
        else:
            logging.debug("Starting main thread in non-blocking mode")
            main_thread = threading.Thread(
                target=self.main_thread,
                daemon=True
            )
            main_thread.start()

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
                    self.current.proc.wait()
                    if self.current.proc.poll() > 0:
                        print()
                        logging.error("Source error")
                        print("\n".join(self.current.error_log))
                        print(str(self.current.proc.stderr.read()))
                        print()
                    break
                try:
                    self.encoder.write(data)
                except BrokenPipeError:
                    if self.should_run:
                        self.encoder.proc.wait()
                        print()
                        logging.error("Encoder error")
                        print("\n".join(self.encoder.error_log))
                        print(str(self.encoder.proc.stderr.read()))
                        print()
                        self.stop()
                        # TODO: start encoder again, seek to
                        # the same position and resume
                    else:
                        break
            self.playlist.pop(0)
        logging.debug("Conti main thread terminated")

    def monitor_thread(self):
        while self.should_run:
            while len(self.playlist) < self.playlist_lenght:
                self.append_next_item()
            time.sleep(.1)
        logging.debug("Conti monitor thread terminated")

    def source_progress_thread(self):
        sbuff = b""
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
                        line = sbuff.decode("utf-8")
                        if line.startswith("frame="):
                            m = re.match(r".*frame=\s*(\d+)\s*fps.*", line)
                            if m:
                                current_frame = int(m.group(1))
                                source.position = \
                                    current_frame / source.meta["video/fps_f"]
                                self.progress_handler()
                        elif CONTI_DEBUG["source"]:
                            logging.debug("SOURCE:", line)
                        else:
                            source.error_log.append(line)
                        sbuff = b""
                    else:
                        sbuff += ch
        logging.debug("Conti source progress thread terminated")

    def encoder_progress_thread(self):
        ebuff = b""
        while self.should_run:
            if not self.playlist:
                time.sleep(.01)
                continue

            if self.encoder and self.encoder.proc.stderr:
                try:
                    ch = self.encoder.proc.stderr.read(1)
                except Exception:
                    log_traceback()
                else:
                    if ch in [b"\n", b"\r"]:
                        line = ebuff.decode("utf-8")
                        if line.startswith("frame="):
                            pass
                            # TODO: get fps/speed value to track performance

                        else:
                            if CONTI_DEBUG["encoder"]:
                                logging.debug("ENCODER:", line)
                            self.encoder.error_log.append(str(line))
                            if len(self.encoder.error_log) > 100:
                                self.encoder.error_log = \
                                    self.encoder.error_log[-100:]

                        ebuff = b""
                    else:
                        ebuff += ch
        logging.debug("Conti encoder progress thread terminated")

    def progress_handler(self):
        return

    def stop(self):
        logging.warning("Stopping playback")
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
