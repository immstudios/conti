from .ffprobe import ffprobe

__all__ = ["check_track_durations"]


def check_track_durations(source_path: str):
    data = ffprobe(source_path)
    durations = set()
    container_duration = data.get("format", {}).get("duration", 0)
    for stream in data["streams"]:
        if stream["codec_type"] not in ["audio", "video"]:
            continue
        durations.add(stream.get("duration", container_duration))

    res = len(durations) == 1
    # if not res:
    #     logger.warning(f"{source_path} tracks duration mismatch: {durations}")
    return res
