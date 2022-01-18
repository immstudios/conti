import os


DEVNULL = open(os.devnull, 'w')
CONTI_DEBUG = {
    "source": False,
    "encoder": False
}


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
