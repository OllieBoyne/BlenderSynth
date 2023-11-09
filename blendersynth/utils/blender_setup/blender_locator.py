import platformdirs
import os
import configparser
import shutil
import subprocess
import warnings

appname = "blendersynth"
appauthor = "BlenderSynth"
config_dir = platformdirs.user_config_dir(appname, appauthor)
os.makedirs(config_dir, exist_ok=True)
config_file = os.path.join(config_dir, "config.ini")


def is_blender_in_path() -> bool:
    """Check if blender is in the PATH (i.e. can be run from the command line with 'blender')"""
    return shutil.which("blender") is not None


def find_blender_python(blender_path: str) -> str:
    """Given a blender executable, find the python interpreter it uses

    :param blender_path: path to blender executable"""

    if read_from_config("BLENDER_PYTHON_PATH") is not None:
        return read_from_config("BLENDER_PYTHON_PATH")

    # get blender to run script to find python path
    try:
        targ_script = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "blender_python_path.py")
        )
        output = subprocess.check_output(
            [blender_path, "--background", "--python", targ_script]
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Issues with finding blender python path. Error: {e}")

    # read output to find python path
    out = None
    for l in output.decode("utf-8").split("\n"):
        if "PYTHON INTERPRETER" in l:
            out = l.split(": ")[1].strip()
            break

    if out is not None:
        write_to_config("BLENDER_PYTHON_PATH", out)
        return out

    raise Exception("Could not find Python interpreter for Blender.")


def validate_blender_path(blender_path: str) -> bool:
    """Check if `blender_path` is a valid blender executable.

    :param blender_path: path to blender executable"""
    if os.access(blender_path, os.X_OK):
        return True

    return False


def set_blender_path(_blender_path: str = None) -> str:
    """First time set-up of Blender Path. Will try to find Blender path in following order of
    precedence:

    1) Input argument _blender_path
    2) Environment variable `BLENDER_PATH`
    3) Blender in PATH
    4) Ask user for path

    When it finds a valid path, it will save it to the Config file stored in user's `platformdirs.user_config_dir`
    """

    if _blender_path is not None:
        if validate_blender_path(_blender_path):
            blender_path = _blender_path

        elif validate_blender_path(
            _blender_path + ".exe"
        ):  # add .exe if not there (helps os.access checking)
            blender_path = _blender_path + ".exe"

        else:
            raise ValueError(
                f"Provided Blender path, {_blender_path}, is not executable."
            )

    elif os.environ.get("BLENDER_PATH") is not None:
        blender_path = os.environ.get("BLENDER_PATH")

    elif is_blender_in_path():
        blender_path = shutil.which("blender")

    else:
        blender_path = input(
            "Blender not found in PATH or Environment Variable.\nPlease provide path to blender executable: "
        )

    blender_path = os.path.abspath(blender_path)  # make sure it's absolute path

    if not validate_blender_path(blender_path):
        if validate_blender_path(blender_path + ".exe"):
            blender_path += ".exe"

        else:
            raise ValueError(
                f"Provided Blender path, {blender_path}, is not valid as a Blender executable."
            )

    write_to_config("BLENDER_PATH", blender_path)
    return blender_path


def get_blender_path() -> str:
    """Return blender path,
    or None if no config file found"""
    return read_from_config("BLENDER_PATH")


def write_to_config(key, value, section="BLENDER_SETUP"):
    """Load config, and write key value pair to cfg[section]"""
    config = configparser.ConfigParser()

    if os.path.exists(config_file):
        config.read(config_file)

    if section not in config:
        config[section] = {}

    config[section][key] = value

    with open(config_file, "w") as configfile:
        config.write(configfile)


def read_from_config(key, section="BLENDER_SETUP"):
    """Load config, and read value from cfg[section]"""
    config = configparser.ConfigParser()

    if os.path.exists(config_file):
        config.read(config_file)

    if section not in config:
        return None

    if key not in config[section]:
        return None

    return config[section][key]


def remove_from_config(key, section="BLENDER_SETUP"):
    """Load config, and remove key from cfg[section]"""
    config = configparser.ConfigParser()

    if os.path.exists(config_file):
        config.read(config_file)

    if section not in config:
        return None

    if key not in config[section]:
        return None

    del config[section][key]

    with open(config_file, "w") as configfile:
        config.write(configfile)


def remove_config():
    """Remove config file"""
    if os.path.exists(config_file):
        os.remove(config_file)
