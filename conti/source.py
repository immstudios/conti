import sys
import subprocess

from .common import *

class ContiSource(object):
    def __init__(self, path, **kwargs):
        self.path = path
        self.proc = None
        self.base_name = get_base_name(path)

    def __repr__(self):
        return "<Conti source: {}>".format(self.base_name)

    @property
    def is_running(self):
        if not self.proc:
            return False
        if self.proc.poll() == None:
            return True
        return False

    def open(self):
        cmd = [
                "ffmpeg",
                "-i", self.path,
                "-pix_fmt", "yuv420p",
                "-s", "1920x1080",
                "-r", "25",
                "-ar", "48000",
                "-c:v", "rawvideo",
                "-c:a", "pcm_s16le",
                "-f", "avi",
                "-"
            ]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=DEVNULL)

    def close(self):
        logging.info("Closing {}".format(self))
        if self.is_running:
            logging.info("Killing {}".format(self))
            self.proc.kill()
        self.proc = None

    def read(self, *args, **kwargs):
        if not self.proc:
            self.open()
        data = self.proc.stdout.read(*args, **kwargs)
        if not data:
            self.close()
            return None
        return data
