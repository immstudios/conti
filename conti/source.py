__all__ = ["ContiSource"]

import os
import signal
import subprocess

from nxtools import get_base_name, logging

from .probe import media_probe
from .filters import (
    FilterChain,
    RawFilter,
    FNull,
    FApad,
    FAtrim
)


class ContiSource(object):
    def __init__(self, parent, path, **kwargs):
        self.parent = parent
        self.path = path
        self.proc = None
        self.base_name = get_base_name(path)
        self.mark_in = kwargs.get("mark_in", 0)
        self.mark_out = kwargs.get("mark_out", 0)
        self.position = 0.0
        self.error_log = []

        self.meta = {}
        self.probed = False
        if "meta" in kwargs:
            assert type(kwargs["meta"]) == dict
            self.meta.update(kwargs["meta"])

        self.filter_chain = FilterChain()

        tracks = {k["index"]: k["channels"] for k in self.audio_tracks}

        if tracks:
            amerge = ""
            num_channels = 0
            for idx in tracks:
                amerge += "[0:{}]".format(idx)
                num_channels += tracks[idx]
            if len(tracks) == 1:
                amerge = "[0:{}]".format(idx)
            else:
                amerge += "amerge=inputs={},".format(len(tracks))

            amerge += "pan=hexadecagonal|{}[audio]".format(
                "|".join([
                    "c{}=c{}".format(idx, idx)
                    for idx in range(num_channels)
                ])
            )
        else:
            amerge = "anullsrc=channel_layout=hexadecagonal"
            amerge += ":sample_rate=48000[audio]"

        self.filter_chain.add(RawFilter(amerge))

        if not self.parent.settings["audio_only"]:
            if self.video_index > -1:
                self.filter_chain.add(
                    FNull("0:{}".format(self.video_index), "video")
                )
            else:
                self.filter_chain.add(RawFilter("color=c=black:s={}x{}".format(
                   self.parent.settings["width"],
                   self.parent.settings["height"]
                )))

    #
    # Class stuff
    #

    def __repr__(self):
        try:
            return "<Conti source: {}>".format(self.base_name)
        except Exception:
            return super(ContiSource, self).__repr__()

    #
    # Metadata helpers
    #

    def load_meta(self):
        self.meta = media_probe(self.path)
        if not self.meta:
            raise IOError(f"Unable to open {self.path}")
        self.probed = True

    @property
    def original_duration(self):
        if "duration" not in self.meta:
            self.load_meta()
        return self.meta["duration"]

    @property
    def audio_tracks(self):
        if not ("audio_tracks" in self.meta and self.probed):
            self.load_meta()
        return self.meta.get("audio_tracks", [])

    @property
    def duration(self):
        return (self.mark_out or self.original_duration) - self.mark_in

    @property
    def video_codec(self):
        if not ("video/codec" in self.meta and self.probed):
            self.load_meta()
        return self.meta["video/codec"]

    @property
    def video_index(self):
        if not ("video/index" in self.meta and self.probed):
            self.load_meta()
        return self.meta.get("video/index", -1)

    #
    # Process control
    #

    @property
    def is_running(self):
        if not self.proc:
            return False
        if self.proc.poll() is None:
            return True
        return False

    def read(self, *args, **kwargs):
        if not self.proc:
            self.open()
        data = self.proc.stdout.read(*args, **kwargs)
        if not data:
            return None
        return data

    def open(self):
        conti_settings = self.parent.settings
        cmd = ["ffmpeg", "-hide_banner"]

        if self.mark_in:
            cmd.extend(["-ss", str(self.mark_in)])
        cmd.extend(["-i", self.path])

        self.filter_chain.add(
            FApad("audio", "audio", whole_dur=self.duration)
        )
        self.filter_chain.add(
            FAtrim("audio", "audio", duration=self.duration)
        )

        cmd.extend([
                "-filter_complex", self.filter_chain.render(),
                "-t", str(self.duration)
            ])

        if not conti_settings["audio_only"]:
            cmd.extend([
                "-map", "[video]",
                "-c:v", "rawvideo",
                "-s", "{}x{}".format(
                    conti_settings["width"],
                    conti_settings["height"]
                ),
                "-pix_fmt", conti_settings["pixel_format"],
                "-r", str(conti_settings["frame_rate"]),
            ])
        else:
            cmd.append("-vn")

        cmd.extend([
                "-map", "[audio]",
                "-c:a", conti_settings["audio_codec"],
                "-ar", str(conti_settings["audio_sample_rate"]),
                "-max_interleave_delta", "400000",
                "-f", "avi",
                "-"
            ])

        logging.debug("Executing", " ".join(cmd))
        self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )

    def stop(self):
        if not self.proc:
            return
        logging.warning("Terminating source process")
        os.kill(self.proc.pid, signal.SIGKILL)
        self.proc.wait()

    def send_command(self, cmd):
        if not self.proc:
            return
        self.proc.stdin.write("C{}\n".format(cmd))
