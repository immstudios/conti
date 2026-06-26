__all__ = ["ffprobe"]

import json
import os
import subprocess
from typing import Any


def ffprobe(input_file: str) -> dict[str, Any]:
    """
    Extract metadata from a media file using ffprobe
    and returns a dictionary object with the result

    Args:
        input_file (str):
            Path to the media file
    Returns:
        dict: metadata
    """
    exists = os.path.exists(input_file)
    path = input_file
    if not exists:
        # logger.error(f"ffprobe: file '{input_file}' does not exist")
        return {}
    cmd = ["ffprobe", "-show_format", "-show_streams", "-print_format", "json", path]

    result = subprocess.run(cmd, capture_output=True, check=False)
    if result.returncode != 0:
        return {}

    res = result.stdout.decode("utf-8")
    return json.loads(res)
