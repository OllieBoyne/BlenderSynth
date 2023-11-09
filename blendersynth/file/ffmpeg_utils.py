import ffmpeg
import os


def hstack(
    videos: list, out_path: str, overwrite: bool = True, loglevel: str = "error"
):
    """Horizontally stack videos.

    :param videos: list of video paths
    :param out_path: output video path
    :param overwrite: overwrite existing video file
    :param loglevel: ffmpeg loglevel (see ffmpeg documentation, default error)"""

    (
        ffmpeg.filter([ffmpeg.input(v) for v in videos], "hstack")
        .output(out_path)
        .global_args("-loglevel", loglevel)
        .run(overwrite_output=overwrite)
    )
