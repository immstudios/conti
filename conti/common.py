import os
from nxtools import *

#TODO: python version agnostic hacks
import thread

CONTI_DEBUG = {
        "source" : False,
        "encoder" : False
    }

DEVNULL = open(os.devnull, 'w')

#
# Default settings
#

def get_settings(**kwargs):
    settings = {
        "pipe_path"     : "pipe.nut",   # Use unique path if you run multichannel setup on one machine
        "frame_rate"    : 25,
    }
    settings.update(kwargs)
    return settings


def get_profile(**kwargs):
    settings = {
        "target"        : "rtp://224.0.0.1:2000",
        "width"         : 640,
        "height"        : 360,

        "pixel_format"  : "yuv420p",
        "video_bitrate" : "800k",       # By default, video quality is quite low...
        "video_preset"  : "fast",       # ... because of my aging development machine.
        "video_profile" : "main",
        "video_codec"   : "libx264",    # By default, software encoder is used.
                                        # You may use h264_nvenc if you have modern nVidia card
        "gop_size"      : 50,           # Fixed GOP size is usefull for HLS/DASH streaming
        "audio_codec"   : "libfdk_aac", # You probably do not want to change this
        "audio_bitrate" : "128k",
        "format"        : "rtp_mpegts", # Other options: "flv", "mpegts",... check ffmpeg docs
    }
    settings.update(kwargs)
    return settings
