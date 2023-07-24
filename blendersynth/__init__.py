# First, make sure Blender has been set up properly
import sys
from .utils.blender_setup import check_blender_install

building_docs = 'sphinx' in sys.modules

if not building_docs:
	check_blender_install(blendersynth_from_local='--local' in sys.argv) # check install here

def fix_blender_install(local=False, editable=False):
	check_blender_install(force_all=True, blendersynth_from_local=local, blendersynth_editable=editable)

def fix_blender_modules(local=False, editable=False):
	check_blender_install(force_install_dependencies=True, blendersynth_from_local=local,
						  blendersynth_editable=editable)

from .run.run_this_script import run_this_script

import sys
from .utils.blender_setup.blender_locator import get_blender_path

if building_docs or get_blender_path() == sys.argv[0]:  # if blender is running this script, or if building docs
	import bpy
	from bpy import *
	from .blender.mesh import Mesh
	from .blender.material import Material
	from .blender.curve import Curve
	from .blender import render
	from .blender.compositor.compositor import Compositor
	from .blender import aov
	from .file.dataset_inputs import Inputs, DebugInputs
	from . import file
	from .run.blender_interface import log_event
	from .blender.world import world
	from .blender.light import Light
	from .blender.camera import Camera
	from . import annotations
	from .file.tempfiles import cleanup_temp_files as cleanup

	# set render engine to cycles
	render.set_engine('CYCLES')

	# common aliases
	def load_blend(src):
		return bpy.ops.wm.open_mainfile(filepath=src)

	# Clear default cube and light
	import bpy
	bpy.data.objects['Cube'].select_set(True)
	bpy.data.objects['Light'].select_set(True)
	bpy.ops.object.delete()

else:
	# Imports for non blender
	from .run.run import execute_jobs
	from . import file
