import tempfile
import os

tempdir = os.path.join(tempfile._get_default_tempdir(), "blendersynth")
os.makedirs(tempdir, exist_ok=True)


def create_temp_file(ext=".png"):
    """Create and return a temporary filename that will be in the user's tempdir.
    These can all be cleaned up after use by the `cleanup_temp_files` function.

    :param ext: file extension to use"""

    if not ext.startswith("."):
        ext = "." + ext

    return tempfile.mktemp(dir=tempdir) + ext


def cleanup_temp_files():
    """Delete all temporary files in the `blendersynth` tempdir"""
    for f in os.listdir(tempdir):
        os.remove(os.path.join(tempdir, f))
