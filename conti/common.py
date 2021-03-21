import os
import time
import subprocess

from nxtools import *

if PYTHON_VERSION < 3:
    critical_error("Python 2 is no longer supported")

DEVNULL = open(os.devnull, 'w')
CONTI_DEBUG = {
        "source" : False,
        "encoder" : False
    }

#
# Default settings
#

def get_settings(**kwargs):
    settings = {
        "gpu_id"          : None,
        "playlist_length" : 2,

        # Processing format
        "width"           : 1920,
        "height"          : 1080,
        "frame_rate"      : 25,
        "pixel_format"    : "yuv422p",
        "audio_only"      : False,
        "audio_codec"     : "pcm_s16le",
        "audio_sample_rate" : 48000,
    }

    settings.update(kwargs)
    return settings
