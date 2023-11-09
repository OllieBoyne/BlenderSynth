# First, make sure Blender has been set up properly
import sys
from .utils.blender_setup import check_blender_install


def fix_blender_install(local=False, editable=False):
    check_blender_install(
        force_all=True, blendersynth_from_local=local, blendersynth_editable=editable
    )


def fix_blender_modules(local=False, editable=False):
    check_blender_install(
        force_install_dependencies=True,
        blendersynth_from_local=local,
        blendersynth_editable=editable,
    )


from .run.run_this_script import run_this_script, is_blender_running

from .utils.blender_setup.blender_locator import get_blender_path
from .run.import_handling import conditional_import, IllegalImport
from typing import TYPE_CHECKING

is_building_docs = "sphinx" in sys.modules
is_blender = is_blender_running()
BLENDER_IMPORTS = (
    is_building_docs or is_blender
)  # if blender is running this script, or if building docs

if BLENDER_IMPORTS or TYPE_CHECKING:
    from .blender.mesh import Mesh
    from .blender.material import Material
    from .blender.curve import Curve
    from .blender.other_objects import Empty
    from .blender import render
    from .blender.compositor.compositor import Compositor
    from .blender import aov
    from .file.dataset_inputs import Inputs, DebugInputs
    from .file.tempfiles import cleanup_temp_files
    from .run.blender_interface import log_event
    from .blender.world import world
    from .blender.light import Light
    from .blender.camera import Camera
    from . import annotations
    from .utils import layout
    from .blender import utils as blender_utils

    import mathutils
    import bpy

    # set IllegalImports here to warn users if they access the objects in the wrong python environment
    execute_jobs, install_module = [
        IllegalImport(REQUIRES_BLENDER=False) for _ in range(2)
    ]

else:
    # Vanilla only imports
    from .run.run import execute_jobs
    from .utils.blender_setup.check_blender_install import install_module

    # set IllegalImports here to warn users if they access the objects in the wrong python environment
    (
        Mesh,
        Material,
        Curve,
        Empty,
        render,
        Compositor,
        aov,
        Inputs,
        DebugInputs,
        cleanup_temp_files,
        log_event,
        world,
        Light,
        Camera,
        annotations,
        layout,
        blender_utils,
        *___,
    ) = [IllegalImport() for _ in range(99)]


# Global imports
from . import file

# scripting setup
if is_blender:
    from bpy import *  # import everything from bpy

    def load_blend(src):
        return bpy.ops.wm.open_mainfile(filepath=src)

    # set render engine to cycles
    from .run.pre_ops import on_script_open

    on_script_open()

if not (BLENDER_IMPORTS or TYPE_CHECKING):
    check_blender_install(
        blendersynth_from_local="--local" in sys.argv
    )  # check install here
