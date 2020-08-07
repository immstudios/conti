__all__ = ["ContiEncoder"]

import os
import time
import subprocess
import signal

from .common import *
from .filters import *

class ContiEncoder(object):
    def __init__(self, parent):
        self.parent = parent
        self.pipe = None
        self.proc = None
        self.afilters = FilterChain()
        self.vfilters = FilterChain(FNull("0:v", "main"))

    def __getitem__(self, key):
        return self.parent.settings[key]

    def __del__(self):
        self.stop()

    def stop(self):
        if not self.proc:
            logging.warning("Unable to stop encoder. Not running.")
            return
        logging.warning("Terminating encoder process")
        os.kill(self.proc.pid, signal.SIGKILL)
        self.proc.wait()

    @property
    def pipe_path(self):
        return self.parent.settings["pipe_path"]

    @property
    def is_running(self):
        if not self.proc:
            return False
        if self.proc.poll() == None:
            return True
        return False

    def write(self, data):
        if not self.is_running:
            return
        self.proc.stdin.write(data)

    def start(self):
        cmd = ["ffmpeg", "-hide_banner"]

        if not "decklink" in [profile.get("params", {"f" : None}) for profile in self["outputs"]]:
           cmd.append("-re")

        cmd.extend(["-i", "-"])

        for i, profile in enumerate(self["outputs"]):
            params = profile.get("params", {})
            for key in params:
                cmd.append("-{}".format(key))
                value = params[key]
                if value != None:
                    cmd.append(str(value))

            cmd.append(profile["target"])

        logging.info("Starting encoder with the following setup:\n", " ".join(cmd))
        self.proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stdout=None
            )