import os
import time
import subprocess

from .common import *

class ContiEncoder(object):
    def __init__(self, parent):
        self.parent = parent
        self.pipe = None
        self.proc = None

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
# Not needed anymore, but it is really cool and can become handy some day
#                "-filter:v", "setpts=N/(FRAME_RATE*TB)",
#                "-filter:a", "asetpts=N/(SAMPLE_RATE*TB)",
                "-pix_fmt", self["pixel_format"],
                "-s", "{}x{}".format(self["width"], self["height"]),
                "-r", str(self["frame_rate"]),
                "-g", str(self["gop_size"]),
                "-c:v", self["video_codec"],
                "-b:v", self["video_bitrate"],
                "-c:a", self["audio_codec"],
                "-b:a", self["audio_bitrate"],
            ]

        if self["video_codec"] == "libx264":
            cmd.extend(["-preset:v", self["video_preset"]])
            cmd.extend(["-profile:v", self["video_profile"]])
            cmd.extend(["-x264opts", "keyint=50:min-keyint=50:scenecut=-1".format(self["gop_size"], self["gop_size"])])

        elif self["video_codec"] == "h264_nvenc":
            cmd.extend(["-preset:v", self["video_preset"]])
            cmd.extend(["-strict_gop", "1", "-no-scenecut", "1"])

        cmd.extend(["-f", self["format"], self.parent.target])

        self.proc = subprocess.Popen(cmd, stderr=DEVNULL)

