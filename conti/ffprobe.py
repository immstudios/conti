__all__ = ["ffprobe"]

import json
import os
import subprocess
from typing import Any


def ffprobe(input_file: str, verbose: bool = False) -> dict[str, Any]:
    """
    Extract metadata from a media file using ffprobe
    and returns a dictionary object with the result

    Args:
        input_file (str):
            Path to the media file

        verbose (bool):
            Log the ffprobe command. Default is False

    Returns:
        dict: metadata
    """
    exists = os.path.exists(input_file)
    path = input_file
    if not exists:
        # logger.error(f"ffprobe: file '{input_file}' does not exist")
        return {}
    cmd = ["ffprobe", "-show_format", "-show_streams", "-print_format", "json", path]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        # if verbose:
        #    error_msg = textwrap.indent(result.stderr.decode("utf-8"), "    ")
        #    #logger.error(f"Unable to read media file {input_file}\n\n{error_msg}\n\n")
        # else:
        # logger.warning(f"Unable to read media file {input_file}")
        return {}

    res = result.stdout.decode("utf-8")
    return json.loads(res)
