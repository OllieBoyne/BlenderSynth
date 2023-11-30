import os
import bpy


def load_image(pth: str):
    """Load an image from a path. Use :func:`os.path.abspath` to avoid rel path issues on Windows.

    :param pth: Path to the image

    """
    abs_pth = os.path.abspath(pth)
    return bpy.data.images.load(abs_pth)
