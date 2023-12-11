import subprocess
import os
import sys
from blendersynth.utils.blender_setup.blender_locator import (
    find_blender_python,
    get_blender_path,
    remove_config,
    write_to_config,
    read_from_config,
    remove_from_config,
    set_blender_path,
)

dependencies = [
    "imageio",
    "numpy",
    "platformdirs",
    "tqdm",
    "opencv-python",
    "ffmpeg-python",
    "pyyaml",
    "pydevd-pycharm",
    "debugpy",  # for debugging
]


def setup_blender_stubs(blender_path):
    """Install blender stubs in vanilla python environment,
    for correct Blender version"""

    vanilla_python_executable = sys.executable

    # Get Blender version from the output
    script_code = "import bpy; print('VERSION' + '.'.join(map(str, bpy.app.version)))"
    result = subprocess.run(
        [blender_path, "--background", "--python-expr", script_code],
        capture_output=True,
        text=True,
    )

    for line in result.stdout.split("\n"):
        if line.startswith("VERSION"):
            blender_version = line[len("VERSION") :].strip()
            break
    else:
        raise Exception("Could not get Blender version")

    # Install stubs
    # Should really use blender_version here
    if not check_module(vanilla_python_executable, "blender-stubs"):
        _install_module(vanilla_python_executable, "blender-stubs")


def check_module(python_executable, module_name):
    try:
        subprocess.check_call(
            [python_executable, "-m", "pip", "show", module_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _install_module(
    python_executable,
    module_name,
    is_test_pypi=False,
    version=None,
    upgrade=True,
    editable=False,
):
    commands = [python_executable, "-m", "pip"]
    commands += ["install"]
    if is_test_pypi:
        commands += ["-i", "https://test.pypi.org/simple/"]

    if editable:
        commands += ["-e"]

    commands += [module_name + (f"=={version}" if version is not None else "")]
    if upgrade:
        commands += ["--upgrade"]

    try:
        subprocess.check_call(commands)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Could not install {module_name} via pip. Error: {e}")


def install_module(
    module_name: str, version: str = None, upgrade: bool = True, editable: bool = False
):
    """Install a module to Blender Python.

    :param module_name: name of module to install
    :param version: version of module to install
    :param upgrade: if True, will upgrade module if it is already installed
    :param editable: if True, will install module in editable mode
    """

    python_exec = find_blender_python(get_blender_path())

    _install_module(
        python_exec, module_name, version=version, upgrade=upgrade, editable=editable
    )


def check_blender_install(
    force_all=False,
    force_find_blender=False,
    force_find_blender_python=False,
    force_install_dependencies=False,
    blendersynth_from_local=False,
    blendersynth_editable=False,
):
    """Check if Blender is installed correctly and has all necessary packages.
    If not, run first time setup.

    On first time setup, will create a file, config.ini, in the user's config,
    containing the necessary info.

    Force: if True, will run first time setup (overwriting any existing config.ini)
    regardless"""

    if force_all:
        remove_config()  # remove config file if it exists to force first time setup

    if force_find_blender:
        remove_from_config("BLENDER_PATH")
    if force_find_blender_python:
        remove_from_config("BLENDER_PYTHON_PATH")
    if force_install_dependencies:
        remove_from_config("DEPENDENCIES_INSTALLED")

    blender_path = get_blender_path()
    if blender_path is None:
        blender_path = set_blender_path()

    setup_blender_stubs(blender_path)  # check blender stubs

    python_path = find_blender_python(blender_path)

    if not read_from_config("DEPENDENCIES_INSTALLED") == "True":
        # check if blender's python has all necessary packages
        for dependency in dependencies:
            if not check_module(python_path, dependency):
                _install_module(python_path, dependency)

        # First uninstall blendersynth if present (in case of updates)
        if check_module(python_path, "blendersynth"):
            subprocess.check_call(
                [python_path, "-m", "pip", "uninstall", "-y", "blendersynth"]
            )

        # Install blendersynth package to blender's python
        if blendersynth_from_local:
            # Install from local setup.py
            setup_py_loc = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "setup.py"
            )
            directory_loc = os.path.dirname(setup_py_loc)
            _install_module(python_path, directory_loc, editable=blendersynth_editable)

        else:
            # Install from pypi
            _install_module(python_path, "blendersynth", upgrade=True)

        write_to_config("DEPENDENCIES_INSTALLED", "True")
