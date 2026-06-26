#!/usr/bin/env python3

import json
import logging
import os
import sys
from typing import Any

from conti import Conti, ContiSource
from conti.filters import FDrawText, FOverlay, FSource

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

#
# Default settings
#

settings: dict[str, Any] = {
    "media_dir": "data",
    "outputs": [
        {
            "target": "rtp://224.0.0.1:2000",
            "audio_filters": "pan=stereo|c0=c0|c1=c1, loudnorm=I=-23",
            "params": {
                "c:v": "h264_nvenc",
                "b:v": "1200k",
                "c:a": "aac",
                "b:a": "128k",
                "f": "rtp_mpegts",
                "pix_fmt": "yuv420p",
            },
        }
    ],
}


#
# Load custom settings from file
#

settings_file = "settings-sdl.json"
if os.path.exists(settings_file) and "--default" not in sys.argv:
    try:
        with open(settings_file) as settings_handle:
            custom_settings = json.load(settings_handle)
    except Exception:
        logger.exception("Unable to parse 'settings.json' file")
        sys.exit(1)
    else:
        settings.update(custom_settings)


#
# Clips library and "playlist" engine
#


class Clips:
    """
    This helper class collects clips from your data directory
    and provides get_next method. This method returns a ContiSource
    object for clip, which should be playing next :)

    In this example, it just iterates over the list of your media
    files in infinite loop.

    """

    def __init__(self, data_dir):
        self.clips = []
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.lower().endswith((".mov", ".mxf")):
                    self.clips.append(os.path.join(root, file))

        if not self.clips:
            logger.error("There are no media files in '{data_dir}'")
            sys.exit(1)
        self.current_index = 0

    def get_next(self, conti):
        path = self.clips[self.current_index % len(self.clips)]
        self.current_index += 1
        source = ContiSource(conti, path)

        # Warning: Filters engine is subject of change
        source.filter_chain.add(
            FDrawText(
                "video",
                "video",
                text=os.path.basename(path),
                fontsize=48,
                fontcolor="white",
                x="(w/2) - (tw/2)",
                y="2*lh",
                box=1,
                boxborderw=8,
                boxcolor="black",
            )
        )

        return source


if __name__ == "__main__":
    clips = Clips(settings["media_dir"])
    conti = Conti(clips.get_next, logger=logger, **settings)

    # station logo burn-in
    logo_path = "data/logo.png"
    if os.path.exists(logo_path):
        conti.filter_chain.add(
            FSource(logo_path, "watermark"),
            FOverlay("video", "watermark", "video"),
        )
    conti.start()
