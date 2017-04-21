import os
from nxtools import *

DEVNULL = open(os.devnull, 'w')

def get_settings(**kwargs):
    settings = {
        "pipe_path"     : "pipe.nut",   # Use unique path if you run multichannel setup on one machine
        "video_bitrate" : "800k",       # By default, video quality is quite low...
        "video_preset"  : "fast",       # ... because of my aging development machine.
        "video_profile" : "main",
        "video_codec"   : "libx264",    # By default, software encoder is used.
                                        # You may use h264_nvenc if you have modern nVidia card
        "width"         : 640,
        "height"        : 360,
        "frame_rate"    : 25,
        "gop_size"      : 50,           # Fixed GOP size is usefull for HLS/DASH streaming
        "audio_codec"   : "libfdk_aac", # You probably do not want to change this
        "audio_bitrate" : "128k",
        "format"        : "rtp_mpegts", # Other options: "flv", "mpegts",... check ffmpeg docs
    }
    settings.update(kwargs)
    return settings

