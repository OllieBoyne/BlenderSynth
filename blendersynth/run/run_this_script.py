"""Quick utility to run the current script from Blender"""
import subprocess
import inspect
import sys
import os
from ..utils.blender_setup.blender_locator import get_blender_path
from ..file.tempfiles import create_temp_file, cleanup_temp_files as cleanup
from shutil import copyfile
import argparse


def _copy_over_script(filepath: str) -> str:
    """Copies over a python script to a tempfile, returning the path.
    Removes certain lines so it can run in blender"""
    remove_lines_containing = [".run_this_script"]
    new_lines = []
    with open(filepath, "r") as f:
        lines = f.readlines()
        for line in lines:
            if not any([s in line for s in remove_lines_containing]):
                new_lines.append(line)

    new_filepath = create_temp_file(ext=".py")
    with open(new_filepath, "w") as f:
        f.writelines(new_lines)

    return new_filepath


def is_blender_running():
    """Returns True if blender is running, False otherwise"""
    try:
        import bpy

        return bpy.__file__ is not None
    except:
        return False


def run_this_script(
    *args,
    open_blender: bool = False,
    debug: bool = False,
    IDE: str = "PyCharm",
    port: int = 5678,
    host: str = "localhost",
    blend_src: str = None,
    blend_as_copy: bool = False,
    **kwargs,
):
    """Run the script in which this function is called from Blender.

    :param open_blender: If True, open a Blender instance after all code is executed, otherwise run in background
    :param debug: If True, will run in debug mode
    :param IDE: IDE to use for debugging. Currently only PyCharm and VSCode are supported
    :param port: Port to use for debugging
    :param host: Host to use for debugging
    :param blend_src: Path to blend file to open (note: this is preferable to `blendersynth.load_blend` as it handles context better)
    :param blend_as_copy: If True, will copy `blend_src` to a temp file before opening - this is useful if you want to make sure you don't accidentally override your `blend_src` file

    args & kwargs are passed to the script being run as command line arguments.

    The flag `--run_this_script` is passed to the script being run to indicate that it is being run from `run_this_script`.
    Use function `is_from_run_this_script` to check if the script is being run from `run_this_script`.
    """
    running_in_blender = is_blender_running()

    caller_path = inspect.stack()[
        1
    ].filename  # path of script that called this function

    if not running_in_blender:  # if blender is not running this script
        caller_dir = os.path.dirname(caller_path)
        env = os.environ.copy()
        env["PYTHONPATH"] = caller_dir + os.pathsep + env.get("PYTHONPATH", "")

        blender_path = get_blender_path()

        # Dump current sys.path to a tempfile so it can be loaded in.
        sys_path = create_temp_file(ext=".txt")
        with open(sys_path, "w") as file:
            for path in sys.path:
                file.write(path + "\n")

        if blend_src is not None and blend_as_copy:
            new_filepath = create_temp_file(ext=".blend")
            copyfile(blend_src, new_filepath)
            blend_src = new_filepath

        commands = (
            [blender_path]
            + [blend_src] * (blend_src is not None)
            + ["--background"] * (not open_blender)
            + ["--python", caller_path, "--"]
        )

        for arg in args:
            commands += [f"--{arg}"]

        for key, value in kwargs.items():
            commands += [f"--{key}", str(value)]

        if sys_path is not None:
            commands += ["--sys_path", sys_path]

        commands += [
            "--run_this_script"
        ]  # flag to indicate that this is being run from run_this_script

        subprocess.call(commands, env=env)

        cleanup()  # cleanup temp files
        sys.exit()  # exit the script once blender is finished

    else:
        if debug:
            IDE = IDE.lower()
            assert IDE in [
                "pycharm",
                "vscode",
            ], f"IDE `{IDE}` not supported, only PyCharm and VSCode are supported"

            if IDE == "pycharm":
                import pydevd_pycharm

                pydevd_pycharm.settrace(
                    host,
                    port=port,
                    stdoutToServer=True,
                    stderrToServer=True,
                    suspend=False,
                )

            elif IDE == "vscode":
                import debugpy

                debugpy.listen((host, port))
                debugpy.wait_for_client()

        # Load sys.path from tempfile
        sys_path = sys.argv[sys.argv.index("--sys_path") + 1]
        with open(sys_path, "r") as file:
            for path in file:
                sys.path.append(path.strip())


def is_from_run_this_script():
    """Returns True if this script is being run from run_this_script"""
    return "--run_this_script" in sys.argv


class ArgumentParser(argparse.ArgumentParser):
    """Subclass of ArgumentParser to properly handle arguments passed through to Blender."""

    _REMOVE_KWARGS = ['--sys_path']
    _REMOVE_ARGS = ['--run_this_script']

    def parse_args(self, args = None, namespace = None):
        if not is_blender_running():
            return super().parse_args(args, namespace)

        else:
            argv = sys.argv[sys.argv.index('--') + 1:]

            # Remove arguments that are not meant for the script
            for arg in self._REMOVE_KWARGS:
                if arg in argv:
                    idx = argv.index(arg)
                    argv.pop(idx)
                    argv.pop(idx)

            for arg in self._REMOVE_ARGS:
                if arg in argv:
                    argv.remove(arg)

            return super().parse_args(argv, namespace)