from nxtools import logging
from nxtools.media import ffprobe

__all__ = ["check_track_durations"]


def check_track_durations(source_path):
    data = ffprobe(source_path)
    durations = set()
    container_duration = data.get("duration", 0)
    for stream in data["streams"]:
        if not stream["codec_type"] in ["audio", "video"]:
            continue
        durations.add(stream.get("duration", container_duration))

    res = len(durations) == 1
    if not res:
        logging.warning(f"{source_path} tracks duration mismatch: {durations}")
    return res
