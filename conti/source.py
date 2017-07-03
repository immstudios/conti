import sys
import subprocess

from .common import *
from .filters import FilterChain, FApad
from .probe import media_probe

class ContiSource(object):
    def __init__(self, path, **kwargs):
        self.path = path
        self.proc = None
        self.base_name = get_base_name(path)
        self.mark_in = kwargs.get("mark_in", 0)
        self.mark_out = kwargs.get("mark_out", 0)

        self.meta = {}
        if "meta" in kwargs:
            assert type(kwargs["meta"]) == dict
            self.meta.update(kwargs["meta"])

        self.vfilters = FilterChain()
        self.afilters = FilterChain()

    #
    # Class stuff
    #

    def __repr__(self):
        try:
            return "<Conti source: {}>".format(self.base_name)
        except:
            return super(ContiSource, self).__repr__()

    def __del__(self):
        logging.info("Closing {}".format(self))
        if self.is_running:
            logging.info("Killing {}".format(self))
            self.proc.kill()

    #
    # Metadata helpers
    #

    def load_meta(self):
        self.meta = media_probe(self.path)
        if not self.meta:
            raise IOError, "Unable to open {}".format(self.path)

    @property
    def original_duration(self):
        if not "duration" in self.meta:
            self.load_meta()
        return self.meta["duration"]

    @property
    def duration(self):
        return (self.mark_out or self.original_duration) - self.mark_in

    @property
    def video_codec(self):
        if not "video/codec" in self.meta:
            self.load_meta()
        return self.meta["video_codec"]

    #
    # Process control
    #

    @property
    def is_running(self):
        if not self.proc:
            return False
        if self.proc.poll() == None:
            return True
        return False

    def read(self, *args, **kwargs):
        if not self.proc:
            self.open()
        data = self.proc.stdout.read(*args, **kwargs)
        if not data:
            return None
        return data


    def open(self, parent):
        conti_settings = parent.settings
        cmd = ["ffmpeg"]

        if HAS_NVIDIA:
            pass
            #TODO:
            # Detect source codec and use hardware accelerated decoding if supported
            # if self.video_codec == ""

        if self.mark_in:
            cmd.extend(["-ss", str(self.mark_in)])

        cmd.extend(["-i", self.path])


        # Add audio padding
        audio_sink = "out" if self.afilters else "in"
        self.afilters.add(FApad(audio_sink, "out"))

        # Render audio filters
        afilters = self.afilters.render()
        cmd.extend(["-filter:a", afilters])

        # Render video filters
        if self.vfilters:
            vfilters = self.vfilters.render()
            cmd.extend(["-filter:v", vfilters])

        cmd.extend([
                "-pix_fmt", conti_settings["pixel_format"],
                "-s", "{}x{}".format(conti_settings["width"], conti_settings["height"]),
                "-r", str(conti_settings["frame_rate"]),
                "-ar", str(conti_settings["audio_sample_rate"]),
                "-t", str(self.duration),
                "-c:v", "rawvideo",
                "-c:a", "pcm_s16le",
                "-f", "avi",
                "-"
            ])
        stderr = None if CONTI_DEBUG["source"] else DEVNULL
        logging.debug("Executing", " ".join(cmd))
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr)
