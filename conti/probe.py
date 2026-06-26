__all__ = ["AudioTrack", "media_probe"]

from typing import Any

from .common import tc2s
from .ffprobe import ffprobe

COMMON_ASPECT_RATIOS = [(1, 1), (4, 3), (16, 9), (2.35, 1)]


class AudioTrack(dict):
    def __repr__(self):
        return "Audio track {index} ({channel_layout})".format(**self)

    @property
    def id(self):
        return self["index"]


def guess_aspect(w: float, h: float) -> str | None:
    if 0 in [w, h]:
        return None
    ratio = float(w) / float(h)
    return "{}/{}".format(
        *min(COMMON_ASPECT_RATIOS, key=lambda x: abs((float(x[0]) / x[1]) - ratio))
    )


def find_start_timecode(probe_result):
    tc_places = [
        probe_result["format"].get("tags", {}).get("timecode", "00:00:00:00"),
        probe_result["format"].get("timecode", "00:00:00:00"),
    ]
    tc = "00:00:00:00"
    for tcp in tc_places:
        if tcp != "00:00:00:00":
            tc = tcp
            break
    return tc


def media_probe(source_path) -> dict[str, Any]:
    probe_result = ffprobe(source_path)
    if not probe_result:
        return {}

    format_info = probe_result["format"]
    meta: dict[str, Any] = {"audio_tracks": []}
    source_vdur = 0
    source_adur = 0

    for stream in probe_result["streams"]:
        if stream["codec_type"] == "video":
            # Frame rate detection
            fps_n, fps_d = [float(e) for e in stream["r_frame_rate"].split("/")]
            meta["video/fps_f"] = fps_n / fps_d
            meta["video/fps"] = f"{int(fps_n)}/{int(fps_d)}"

            # Aspect ratio detection
            try:
                dar_n, dar_d = [
                    float(e) for e in stream["display_aspect_ratio"].split(":")
                ]
                if not (dar_n and dar_d):
                    raise ValueError("Invalid DAR values")
            except Exception:
                dar_n, dar_d = float(stream["width"]), float(stream["height"])

            meta["video/aspect_ratio_f"] = float(dar_n) / dar_d
            meta["video/aspect_ratio"] = guess_aspect(dar_n, dar_d)

            try:
                source_vdur = float(stream["duration"])
            except Exception:
                source_vdur = 0

            meta["video/codec"] = stream["codec_name"]
            meta["video/pixel_format"] = stream["pix_fmt"]
            meta["video/width"] = int(stream["width"])
            meta["video/height"] = int(stream["height"])
            meta["video/index"] = int(stream["index"])
            meta["video/color_range"] = stream.get("color_range", "")
            meta["video/color_space"] = stream.get("color_space", "")
            meta["video/nb_frames"] = int(stream.get("nb_frames", 0))

        elif stream["codec_type"] == "audio":
            meta["audio_tracks"].append(AudioTrack(**stream))
            try:
                source_adur = max(source_adur, float(stream["duration"]))
            except Exception:
                pass

    if meta.get("video/nb_frames", False):
        meta["duration"] = meta["video/nb_frames"] / meta["video/fps_f"]
    else:
        meta["duration"] = float(format_info["duration"]) or source_vdur or source_adur

    tc = find_start_timecode(probe_result)
    if tc != "00:00:00:00":
        meta["start_timecode"] = tc2s(tc)  # TODO: fps
    return meta
