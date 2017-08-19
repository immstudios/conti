import os
import time
import subprocess

from .common import *
from .filters import FilterChain

class ContiEncoder(object):
    def __init__(self, parent):
        self.parent = parent
        self.pipe = None
        self.proc = None
        self.afilters = FilterChain()
        self.vfilters = FilterChain()

    def __getitem__(self, key):
        return self.parent.settings[key]

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
        if not self.pipe:
            self.pipe = open(self.pipe_path, "wb")
        self.pipe.write(data)

    def start(self):
        if os.path.exists(self.pipe_path):
            os.remove(self.pipe_path)
        os.mkfifo(self.pipe_path)

        cmd = [
                "ffmpeg",
                "-re",
                "-i", self.pipe_path,
            ]

        for output_settings in self["outputs"]:
            profile = get_profile(**output_settings)

            if profile["video_codec"]:
                if self.vfilters:
                    vfilters = self.vfilters.render()
                    cmd.extend(["-filter:v", vfilters])

                cmd.extend(["-pix_fmt", profile["pixel_format"]])
                cmd.extend(["-s", "{}x{}".format(profile["width"], profile["height"])])
                cmd.extend(["-g", str(profile["gop_size"])])
                cmd.extend(["-c:v", profile["video_codec"]])
                cmd.extend(["-b:v", profile["video_bitrate"]])

                if profile["video_codec"] == "libx264":
                    cmd.extend(["-preset:v", profile["video_preset"]])
                    cmd.extend(["-profile:v", profile["video_profile"]])
                    cmd.extend(["-x264opts", "keyint=50:min-keyint=50:scenecut=-1".format(profile["gop_size"], profile["gop_size"])])

                elif profile["video_codec"] == "h264_nvenc":
                    cmd.extend(["-preset:v", profile["video_preset"]])
                    cmd.extend(["-strict_gop", "1", "-no-scenecut", "1"])


            if profile["audio_codec"]:
                if self.afilters:
                    afilters = self.afilters.render()
                    cmd.extend(["-filter:a", afilters])
                cmd.extend(["-c:a", profile["audio_codec"]])
                cmd.extend(["-b:a", profile["audio_bitrate"]])

            default_profile = get_profile()
            for key in profile:
                if not key in default_profile:
                    cmd.append("-{}".format(key))
                    value = profile[key]
                    if value != None:
                        cmd.append(str(value))

            cmd.extend(["-f", profile["format"], profile["target"]])

        stderr = None if CONTI_DEBUG["encoder"] else DEVNULL
        self.proc = subprocess.Popen(cmd, stderr=stderr)
