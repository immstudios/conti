__all__ = ["ContiEncoder"]

import os
import time
import subprocess
import signal

from .common import *
from .filters import *

class ContiEncoder(object):
    def __init__(self, parent):
        self.parent = parent
        self.pipe = None
        self.proc = None
        self.afilters = FilterChain()
        self.vfilters = FilterChain(FNull("0:v", "main"))

    def __getitem__(self, key):
        return self.parent.settings[key]

    def __del__(self):
        self.stop()

    def stop(self):
        if not self.proc:
            logging.warning("Unable to stop encoder. Not running.")
            return
        logging.warning("Terminating encoder process")
        os.kill(self.proc.pid, signal.SIGKILL)
        self.proc.wait()

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
        if not self.is_running:
            return
        self.proc.stdin.write(data)

    def start(self):
        cmd = ["ffmpeg", "-hide_banner"]
        if not "decklink" in [o["format"] for o in self["outputs"]]:
            cmd.append("-re")

        cmd.extend(["-i", "-"])


        vsink = "main"

        if len(self["outputs"]) > 1:
            self.vfilters.add(FSplit(vsink, [
                "i{}".format(i) for i in range(
                    len(self["outputs"])
                )]))
        else:
            self.vfilters.add(FNull(vsink, "i0"))


        for i, output_settings in enumerate(self["outputs"]):
            profile = get_profile(**output_settings)
            ofilters = []

            if profile["field_order"] == "top":
                ofilters.append("setfield=tff")
            elif profile["field_order"] == "bottom":
                ofilters.append("setfield=bff")

            if profile.get("width", self["width"]) != self["width"] or profile.get("height", self["height"]) != self["height"]:
                ofilters.append("scale={}:{}".format(profile["width"], profile["height"]))

            self.vfilters.add(RawFilter("[i{}]{}[o{}]".format(i, ",".join(ofilters) if ofilters else "null", i)))


        #TODO: add audiofilters to vchain
        filter_chain = self.vfilters.render()
        cmd.extend(["-filter_complex", filter_chain])




        for i, output_settings in enumerate(self["outputs"]):
            profile = get_profile(**output_settings)

            cmd.extend(["-map", "[o{}]".format(i)])
            cmd.extend(["-map", "0:a"]) #TODO: use audio filterchain output

            if profile.get("field_order") == "top":
                profile["field_order"] = "tt"
            elif profile.get("field_order") == "bottom":
                profile["field_order"] = "bb"


            if profile["format"] == "ndi":
                profile["format"] = "libndi_newtek"
                profile["pix_fmt"] = "uyvy422"
                profile["r"] = self["frame_rate"]

            elif profile["format"] == "decklink":
                profile["r"] = self["frame_rate"]
                profile["s"] = "{}x{}".format(self["width"], self["height"])
                profile["pix_fmt"] = profile.get("pix_fmt", "uyvy422")

            else:
                if profile["video_codec"]:


                    cmd.extend(["-pix_fmt", profile.get("pixel_format", "yuv420p")])
                    cmd.extend(["-g", str(profile["gop_size"])])
                    cmd.extend(["-c:v", profile["video_codec"]])
                    cmd.extend(["-b:v", profile["video_bitrate"]])

                    if profile["video_codec"] == "libx264":
                        cmd.extend(["-preset:v", profile["video_preset"]])
                        cmd.extend(["-profile:v", profile["video_profile"]])
                        cmd.extend(["-x264opts", "keyint={}:min-keyint={}:scenecut=-1".format(profile["gop_size"], profile["gop_size"])])

                    elif profile["video_codec"] == "h264_nvenc":
                        cmd.extend(["-preset:v", profile["video_preset"]])
                        cmd.extend(["-strict_gop", "1", "-no-scenecut", "1"])


                if profile["audio_codec"]:
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
        logging.info("Starting encoder with the following setup:\n", " ".join(cmd))
        self.proc = subprocess.Popen(
                cmd,
                stderr=stderr,
                stdin=subprocess.PIPE,
                stdout=None
            )
