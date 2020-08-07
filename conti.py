#!/usr/bin/env python3

import os
import json
import functools

from nxtools import *

from conti import *
from conti.filters import *

CONTI_DEBUG["decoder"] = False
CONTI_DEBUG["encoder"] = True

#
# Default settings
#

settings = {
    "media_dir" : "data/",
    "outputs" : [ {
        "target" : "SDL Output",
        "params" : {
            "f" : "sdl",
            "pix_fmt" : "yuv420p"
        }
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


#
# Clips library and "playlist" engine
#


class Clips(object):
    """
    This helper class collects clips from your data directory
    and provides get_next method. This method returns a ContiSource
    object for clip, which should be playing next :)

    In this example, it just iterates over the list of your media
    files in infinite loop.

    """

    def __init__(self, data_dir):
        self.clips = [f.path for f in get_files(data_dir, exts=["mov"])]
        self.current_index = 0

    def get_next(self, conti):
        path = self.clips[self.current_index % len(self.clips)]
        self.current_index += 1
        source = ContiSource(conti, path)


        # Warning: Filters engine is subject of change
        source.filter_chain.add(
                FDrawText("video", "video",
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

if __name__ == "__main__":
    clips = Clips(settings["media_dir"])
    conti = Conti(clips.get_next, **settings)

    # station logo burn-in
    logo_path = "data/logo.png"
    if os.path.exists(logo_path):
        conti.filter_chain.add(
                FSource(logo_path, "watermark"),
                FOverlay("video", "watermark", "video"),
            )
    conti.start()
