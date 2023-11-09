import json
import os
from typing import Union


def save_label(data: Union[dict, list], pth: str):
    """Save a label to a file.

    :param data: The data to save.
    :param pth: The path to save the data to."""

    os.makedirs(os.path.dirname(pth), exist_ok=True)
    with open(pth, "w") as outfile:
        json.dump(data, outfile)
