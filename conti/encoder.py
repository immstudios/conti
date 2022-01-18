__all__ = ["ContiEncoder"]

import os
import signal
import subprocess

from nxtools import logging

from .filters import (
    FilterChain,
    FNull,
    FANull,
    RawFilter
)


class ContiEncoder(object):
    """Conti encoder process."""
    def __init__(self, parent):
        """ContiEncoder constructor."""
        self.parent = parent
        self.pipe = None
        self.proc = None
        self.error_log = []
        self.filter_chain = FilterChain()

        # TODO: Replace with rawfilter doing something
        # based on conti settings(interlacing and stuff)
        self.filter_chain.add(FNull("0:0", "video"))

        # TODO: Replace with rawfilter doing something
        # based on conti settings(loudness and stuff)
        self.filter_chain.add(FANull("0:1", "audio"))

    def __getitem__(self, key: str):
        """Return Conti settings value."""
        return self.parent.settings[key]

    def get(self, key: str, default: str = None):
        """Return Conti settings value with default."""
        return self.parent.settings.get(key, default)

    def __del__(self):
        """ContiEncoder destructor."""
        self.stop()

    def stop(self):
        """Stop encoder process."""
        if not self.proc:
            logging.warning("Unable to stop encoder. Not running.")
            return
        if self.proc.poll() is not None:
            logging.warning("Unable to stop encoder. Already stopped")
            return
        logging.warning("Terminating encoder process")
        os.kill(self.proc.pid, signal.SIGKILL)
        self.proc.wait()

    @property
    def pipe_path(self):
        """Return pipe path."""
        return self.parent.settings["pipe_path"]

    @property
    def is_running(self):
        """Return True if encoder is running."""
        if not self.proc:
            return False
        if self.proc.poll() is None:
            return True
        return False

    def write(self, data):
        """Write data to encoder process."""
        if not self.is_running:
            return
        self.proc.stdin.write(data)

    def start(self):
        """Start encoder process."""
        cmd = ["ffmpeg", "-hide_banner"]

        # Most of the output formats needs -re switch to keep
        # the encoding speed at real time.
        # With decklink, this is not needed nor desireable

        if "decklink" not in [
            profile.get("params", {"f": None})
            for profile in self["outputs"]
        ]:
            cmd.append("-re")

        # Custom output filterchain

        filters = self.get("audio_filters", [])
        if filters:
            if type(filters) == str:
                filters = [filters]
            self.filter_chain.add(RawFilter(
                "[audio]" + ",".join(filters) + "[audio]"
                ))

        pre_filters = self.get("pre_filters", [])
        if pre_filters:
            if type(pre_filters) == str:
                pre_filters = [pre_filters]
            for pf in pre_filters:
                self.filter_chain.add(RawFilter(pf))

        filters = self.get("video_filters", [])
        if filters:
            if type(filters) == str:
                filters = [filters]
            self.filter_chain.add(RawFilter(
                "[video]" + ",".join(filters) + "[video]"
                ))

        # Split video and audio outputs to match needed count.
        # If there is no video or audio needed in the output profiles,
        # send output to nullsink or anullsink

        voutputs = []
        aoutputs = []
        for i, profile in enumerate(self["outputs"]):
            if profile.get("video", True):
                voutputs.append(i)
            if profile.get("audio", True):
                aoutputs.append(i)

        if voutputs:
            vsplit = "[video]split={}".format(len(voutputs))
            for voutput in voutputs:
                vsplit += "[video{}]".format(voutput)
            self.filter_chain.add(RawFilter(vsplit))
        else:
            self.filter_chain.add(RawFilter("[video]nullsink"))

        if aoutputs:
            asplit = "[audio]asplit={}".format(len(aoutputs))
            for aoutput in aoutputs:
                asplit += "[audio{}]".format(aoutput)
            self.filter_chain.add(RawFilter(asplit))
        else:
            self.filter_chain.add(RawFilter("[audio]anullsink"))

        # Per-output stream filterchain

        for i, profile in enumerate(self["outputs"]):
            vfilters = profile.get("video_filters", [])
            afilters = profile.get("audio_filters", [])
            if vfilters:
                if type(vfilters) == str:
                    vfilters = [vfilters]
                self.filter_chain.add(RawFilter(
                    "[video{}]".format(i) +
                    ",".join(vfilters) +
                    "[video{}]".format(i)
                    ))
            if afilters:
                if type(afilters) == str:
                    afilters = [afilters]
                self.filter_chain.add(RawFilter(
                    "[audio{}]".format(i) +
                    ",".join(afilters) +
                    "[audio{}]".format(i)
                    ))

        # Load AV stream from pipe and attach the finished filterchain

        cmd.extend([
            "-i", "-",
            "-filter_complex", self.filter_chain.render(),
        ])

        # Create output profiles

        for i, profile in enumerate(self["outputs"]):

            if self.parent.settings["audio_only"]:
                cmd.extend(["-map", "[audio]"])
            else:
                if profile.get("video", True):
                    cmd.extend(["-map", "[video{}]".format(i)])
                if profile.get("audio", True):
                    cmd.extend(["-map", "[audio{}]".format(i)])

            params = profile.get("params", {})
            for key in params:
                cmd.append("-{}".format(key))
                value = params[key]
                if value is not None:
                    cmd.append(str(value))
            cmd.append(profile["target"])

        # ... and start the encoder

        logging.debug(
            "Starting encoder with the following settings:\n",
            " ".join(cmd)
        )
        self.proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stdout=None
            )
