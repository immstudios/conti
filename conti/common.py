import os

CONTI_DEBUG = {"source": False, "encoder": False}


def get_settings(**kwargs):
    """Return a dict with the settings for the conti module."""
    settings = {
        "gpu_id": None,
        "playlist_length": 2,
        # Processing format
        "width": 1920,
        "height": 1080,
        "frame_rate": 25,
        "pixel_format": "yuv422p",
        "audio_only": False,
        "audio_codec": "pcm_s16le",
        "audio_sample_rate": 48000,
    }

    settings.update(kwargs)
    return settings


def get_base_name(path: str) -> str:
    """Return base name of the file without extension."""
    return os.path.splitext(os.path.basename(path))[0]


def tc2s(tc: str, base: float = 25) -> float:
    """Convert an SMPTE timecode (HH:MM:SS:FF) to number of seconds.

    Args:
        tc (str):
            Source timecode

        base (float):
            Frame rate (default: 25)

    Returns:
        float:
            Resulting value in seconds
    """
    tc = tc.replace(";", ":")
    hh, mm, ss, ff = (int(e) for e in tc.split(":"))
    res: float
    res = hh * 3600
    res += mm * 60
    res += ss
    res += ff / float(base)
    return res
