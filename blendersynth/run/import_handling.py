"""For calling errors if a user tries run certain operations in the wrong python environment"""

from importlib import import_module
from typing import Union

package_name = "blendersynth"


def conditional_import(
    condition: bool, src: str, name: str = None
) -> Union["IllegalImport", object]:
    """
    [No longer used in __init__.py, but kept here for reference]
    Imports a module if condition,
    otherwise returns IllegalImport.

    :param condition: If True, import the module
    :param src: The module to import
    :param name: The name of the module to import. If None, the last part of src is used.
    :return: The imported module, or IllegalImport if condition is False
    """

    if condition:
        if src.startswith("."):
            module = import_module(src, package=package_name)
        else:
            module = import_module(src)

        if name is None:
            return module

        return getattr(module, name if name else src.split(".")[-1])
    else:
        return IllegalImport()


class IllegalImport:
    """Object which raises error on any interaction, to tell users they have used BlenderSynth incorrectly."""

    def __init__(self, REQUIRES_BLENDER=True):
        self.REQUIRES_BLENDER = REQUIRES_BLENDER

    def __call__(self, *args, **kwargs):
        raise ImportError(self._message)

    def __getattr__(self, name):
        raise ImportError(self._message)

    @property
    def _message(self):
        if self.REQUIRES_BLENDER:
            return (
                "This object can only be used inside a Blender python environment. "
                "Make sure that either:"
                "\n- bsyn.run_this_script() is run on a previous line"
                "\n- This script is being run from another python script, using bsyn.execute_jobs."
            )

        else:
            return "This object can only be used outside a Blender python environment. "
