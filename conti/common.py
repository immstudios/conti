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
        "gpu_id"        : None,
        "frame_rate"    : 25,
        "width"         : 1920,         # Processing format
        "height"        : 1080,
        "pixel_format"  : "yuv420p",
        "audio_sample_rate" : 48000,
        "use_gpu"       : HAS_NVIDIA
    }
    settings.update(kwargs)
    return settings


def get_profile(**kwargs):
    settings = {
        "format"        : "rtp_mpegts",
        "target"        : "rtp://224.0.0.1:2000",
        "field_order"   : False,


        "video_bitrate" : "4000k",      # By default, video quality is quite low...
        "video_preset"  : "fast",       # ... because of my aging development machine.
        "video_profile" : "main",
        "video_codec"   : "libx264",    # By default, software encoder is used.
                                        # You may use h264_nvenc if you have modern nVidia card
        "gop_size"      : 80,           # Fixed GOP size is usefull for HLS/DASH streaming
        "audio_codec"   : "libfdk_aac", # You probably do not want to change this
        "audio_bitrate" : "128k",
    }
    settings.update(kwargs)
    return settings
