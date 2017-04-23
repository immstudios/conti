#!/usr/bin/env python

import os
import json

import rex

from nxtools import *

from conti import Conti, ContiSource
from conti.filters import *

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
        source =  ContiSource(path)
        source.vfilters.add(
                    FDrawText("in", "out",
                        text=get_base_name(path),
                        fontsize=48,
                        fontcolor="white",
                        x="(w/2) - (tw/2)",
                        y="2*lh",
                        box=1,
                        boxborderw=8,
                        boxcolor="black"
                    )
                )
        return source


settings = {
    "outputs" : [ {
        "target" : "rtp://224.0.0.1:2000&pkt_size=1316"
    }]
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
    conti = Conti(clips.get_next, **settings)

    conti.vfilters.add(
            FSource("data/logo.png", "watermark"),
            FOverlay("in", "watermark", "out"),
            FDrawText("out", "out",
                text="'%{localtime\:%T}'",
                fontsize=48,
                fontcolor="white",
                x="(w/2) - (tw/2)",
                y="h - (2*lh)",
                box=1,
                boxborderw=20,
                boxcolor="black"
            )
        )

    conti.start()
