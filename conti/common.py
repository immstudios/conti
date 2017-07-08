import os
import time
import subprocess

from nxtools import *

if PYTHON_VERSION > 3:
    import _thread as thread
else:
    import thread


DEVNULL = open(os.devnull, 'w')

CONTI_DEBUG = {
        "source" : False,
        "encoder" : False
    }

#
# System check
#

def has_nvidia():
    try:
        p = subprocess.Popen("nvidia-smi", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return False
    while p.poll() == None:
        time.sleep(.1)
    if p.returncode:
        return False
    logging.debug("GPU processing available")
    return True

HAS_NVIDIA = has_nvidia()

#
# Default settings
#

def get_settings(**kwargs):
    settings = {
        "pipe_path"     : "pipe.nut",   # Use unique path if you run multichannel setup on one machine
        "gpu_id"        : None,
        "frame_rate"    : 25,
        "width"         : 1920,         # Processing format
        "height"        : 1080,
        "pixel_format"  : "yuv420p",
        "audio_sample_rate" : 48000
    }
    settings.update(kwargs)
    return settings


def get_profile(**kwargs):
    settings = {
        "target"        : "rtp://224.0.0.1:2000",
        "width"         : 960,
        "height"        : 540,

        "pixel_format"  : "yuv420p",
        "video_bitrate" : "1600k",      # By default, video quality is quite low...
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
