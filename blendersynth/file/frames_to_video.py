import os
import glob
import re
from .tempfiles import create_temp_file
from ..utils.types import Camera
from typing import List

from ..utils import import_module

ffmpeg = import_module("ffmpeg", "ffmpeg-python")


valid_frames_exts = ("png", "jpg", "jpeg", "bmp", "tiff", "tif")


def get_frames_from_directory(directory, exts=valid_frames_exts, sort=True):
    """Return a list of all paths to files in directory which have a valid frame extension"""
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.splitext(f)[-1][1:] in exts
    ]
    if sort:
        files = sorted(files)
    return files


def ffmpeg_input_from_files(file_list, frame_rate=25):
    """Return ffmpeg input from list of files"""
    file_list_loc = create_temp_file(ext=".txt")

    with open(file_list_loc, "w") as f:
        for file in file_list:
            abs_file = os.path.abspath(file)
            f.write(f"file '{abs_file}'\n")

    return ffmpeg.input(file_list_loc, r=str(frame_rate), f="concat", safe="0")


def frames_to_video(
    *args,
    frame_list=None,
    frame_fmt=None,
    directory=None,
    frame_rate=30,
    output_loc="./output.mp4",
    output_fmt="mp4",
    pix_fmt="yuv420p",
    overwrite=True,
    loglevel="error",
    delete_images=False,
):
    """
    Need to input one of frame_list or frame_fmt or directory

    :param frame_list: [optional] list of frames to concatenate into a video
    :param frame_fmt: [optional] frame format to use as input
    :param directory: [optional] directory to use as input (loads sorted images in directory)

    :param frame_rate: frame rate of video
    :param output_loc: video file location
    :param output_fmt: video file format
    :param pix_fmt: pixel format (see ffmpeg documentation, default yuv420p)

    :param overwrite: overwrite existing video file
    :param loglevel: ffmpeg loglevel (see ffmpeg documentation, default error)

    :param delete_images: delete images after video is created
    :return:
    """

    assert args == (), "frames_to_video() takes keyword arguments only"

    # Assert exactly 1 of frame_list, frame_fmt, directory is provided
    assert (
        sum([frame_list is not None, frame_fmt is not None, directory is not None]) == 1
    ), "Exactly one of frame_list, frame_fmt, directory must be provided"

    vid_input = None
    file_list = []
    if frame_list:
        assert frame_list, "No frames provided"
        vid_input = ffmpeg_input_from_files(frame_list, frame_rate=frame_rate)
        file_list = frame_list

    elif frame_fmt:
        vid_input = ffmpeg.input(frame_fmt)

        # Get file list using glob (note: this does not match the exact frame format, so may not be fully robust)
        file_list = glob.glob(re.sub(r"%\d*[df]", "*", frame_fmt))

    elif directory:
        file_list = get_frames_from_directory(directory)
        assert file_list, "No valid frames found in directory"

        vid_input = ffmpeg_input_from_files(file_list, frame_rate=frame_rate)

    (
        vid_input.output(output_loc, format=output_fmt, r=frame_rate, pix_fmt=pix_fmt)
        .global_args("-loglevel", loglevel)
        .run(overwrite_output=overwrite)
    )

    if delete_images:
        for f in file_list:
            os.remove(f)

    print("Video created at " + output_loc)


def frames_to_video_multiview(
    cameras: List[Camera], directory=".", out_loc="vid.mp4", **kwargs
):
    """
    Following the rendering of a multiview animation, this function handles rendering the frames separately into
    videos.

    :param cameras: List of cameras used for rendering
    :param directory: Directory to look for frames in
    :param out_loc: Output location for videos. Each camera will be saved as a separate video with the camera name prepended
    :param kwargs: Keyword arguments to pass to :func:`frames_to_video`
    """

    for cam in cameras:
        frame_files = sorted(
            [
                os.path.join(directory, f)
                for f in os.listdir(directory)
                if f.startswith(cam.name)
            ]
        )
        out_f = os.path.join(
            os.path.dirname(out_loc), f"{cam.name}_{os.path.basename(out_loc)}"
        )
        frames_to_video(frame_list=frame_files, output_loc=out_f, **kwargs)
