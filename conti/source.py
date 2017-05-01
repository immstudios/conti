import sys
import subprocess

from .common import *
from .filters import FilterChain

class ContiSource(object):
    def __init__(self, path, **kwargs):
        self.path = path
        self.proc = None
        self.base_name = get_base_name(path)
        self.vfilters = FilterChain()
        self.afilters = FilterChain()

    def __repr__(self):
        return "<Conti source: {}>".format(self.base_name)

    def __del__(self):
        logging.info("Closing {}".format(self))
        if self.is_running:
            logging.info("Killing {}".format(self))
            self.proc.kill()

    @property
    def is_running(self):
        if not self.proc:
            return False
        if self.proc.poll() == None:
            return True
        return False

    def read(self, *args, **kwargs):
        if not self.proc:
            self.open()
        data = self.proc.stdout.read(*args, **kwargs)
        if not data:
            return None
        return data


    def open(self):
        #TODO: custom intermediate settings
        # frame rate, audio channels count, resolution, pixel format...

        #TODO:
        # Detect source codec and use hardware accelerated decoding if supported

        cmd = [
                "ffmpeg",
                "-i", self.path,
            ]

        if self.afilters:
            afilters = self.afilters.render()
            cmd.extend(["-filter:a", afilters])

        if self.vfilters:
            vfilters = self.vfilters.render()
            cmd.extend(["-filter:v", vfilters])

        cmd.extend([
                "-shortest",
                "-pix_fmt", "yuv420p",
                "-s", "1920x1080",
                "-r", "25",
                "-ar", "48000",
                "-c:v", "rawvideo",
                "-c:a", "pcm_s16le",
                "-f", "avi",
                "-"
            ])
        stderr = None if CONTI_DEBUG["source"] else DEVNULL
        logging.debug("Executing", " ".join(cmd))
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr)
