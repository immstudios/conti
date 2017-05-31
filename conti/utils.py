from nxtools import *
from nxtools.media import *

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
        logging.warning("{} tracks duration mismatch: {}".format(source_path, durations))
    return res

