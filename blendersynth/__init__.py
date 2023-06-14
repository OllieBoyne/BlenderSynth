# First, make sure Blender has been set up properly
from .utils.blender_setup import check_blender_install
check_blender_install() # check install here

def fix_blender_install():
	check_blender_install(force_all=True)

def fix_blender_modules():
	check_blender_install(force_install_dependencies=True)

from .run_this_script import run_this_script

import sys
from .utils.blender_setup.blender_locator import get_blender_path

if get_blender_path() == sys.argv[0]:  # if blender is running this script
	import bpy
	from bpy import *
	from .blender.mesh import Mesh
	from .blender import render
	from .blender.compositor.compositor import Compositor
	from .blender import aov
	from .file.dataset_inputs import INPUTS
	from . import file
	from .run.blender_interface import log_event
	from .blender.world import world
	from .blender.light import Light
	from .blender.camera import Camera
	from . import annotations

	# set render engine to cycles
	render.set_engine('CYCLES')

	# common aliases
	load_blend = bpy.ops.wm.open_mainfile

	# Clear default cube
	import bpy
	bpy.data.objects['Cube'].select_set(True)
	bpy.ops.object.delete()

else:
	# Imports for non blender
	from .run.run import execute_jobs
	from . import file
