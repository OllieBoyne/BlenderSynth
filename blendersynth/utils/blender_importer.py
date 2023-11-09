"""Import python module - if not installed, install it"""

from .blender_setup.check_blender_install import _install_module
import sys


def import_module(named_module, pip_name=None):
    """Import python module - if not installed, install it.

    :param named_module: name of module to import (python name)
    :param pip_name: name of module to install (pip name). If None, will use named_module
    """

    if pip_name is None:
        pip_name = named_module

    try:
        return __import__(named_module)
    except ModuleNotFoundError:
        print(
            f"Blender executable does not have module `{named_module}` installed. Installing..."
        )
        python_exec = sys.executable
        _install_module(python_exec, pip_name)
        return __import__(named_module)
