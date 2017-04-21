#!/usr/bin/env python

import json
import rex

from nxtools import *
from conti import Conti, ContiSource

class Clips(object):
    """
    This helper class collects clips from your data directory
    and provides get_next method. This method returns a ContiSource
    object for clip, which should be playing next :)

    In this example, it just iterates over the list of your media
    files in infinite loop.

    """

    def __init__(self, data_dir):
        self.clips = [f for f in get_files(data_dir, exts=["mov"])]
        self.current_index = 0

    def get_next(self):
        path = self.clips[self.current_index % len(self.clips)]
        self.current_index += 1
        return ContiSource(path)


settings = {
        "target" : "rtp://224.0.0.1:2000&pkt_size=1316",

        # Check conti/common.py for all available settings
        "conti_settings" : {
            }
    }

#
# Load custom settings from file
#

settings_file = "settings.json"
if os.path.exists(settings_file):
    try:
        custom_settings = json.load(open(settings_file))
    except Exception:
        log_traceback()
    else:
        settings.update(custom_settings)



if __name__ == "__main__":
    clips = Clips("data/")

    conti = Conti(clips.get_next, settings["target"], **settings["conti_settings"])
    conti.start()
