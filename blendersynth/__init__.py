# First, make sure Blender has been set up properly
import sys
from .utils.blender_setup import check_blender_install

def fix_blender_install(local=False, editable=False):
	check_blender_install(force_all=True, blendersynth_from_local=local, blendersynth_editable=editable)

def fix_blender_modules(local=False, editable=False):
	check_blender_install(force_install_dependencies=True, blendersynth_from_local=local,
						  blendersynth_editable=editable)

from .run.run_this_script import run_this_script

import sys
from .utils.blender_setup.blender_locator import get_blender_path
from .run.import_handling import conditional_import

is_building_docs = 'sphinx' in sys.modules
is_blender = 'bpy' in sys.modules
IS_BLENDER_RUN = is_building_docs or is_blender  # if blender is running this script, or if building docs


# Blender only imports
Mesh = conditional_import(IS_BLENDER_RUN, '.blender.mesh', 'Mesh')
Material = conditional_import(IS_BLENDER_RUN, '.blender.material', 'Material')
Curve = conditional_import(IS_BLENDER_RUN, '.blender.curve', 'Curve')
Empty = conditional_import(IS_BLENDER_RUN, '.blender.other_objects', 'Empty')
render = conditional_import(IS_BLENDER_RUN, '.blender.render')
Compositor = conditional_import(IS_BLENDER_RUN, '.blender.compositor.compositor', 'Compositor')
aov = conditional_import(IS_BLENDER_RUN, '.blender', 'aov')
Inputs = conditional_import(IS_BLENDER_RUN, '.file.dataset_inputs', 'Inputs')
DebugInputs = conditional_import(IS_BLENDER_RUN, '.file.dataset_inputs', 'DebugInputs')
cleanup_temp_files = conditional_import(IS_BLENDER_RUN, '.file.tempfiles', 'cleanup_temp_files')
log_event = conditional_import(IS_BLENDER_RUN, '.run.blender_interface', 'log_event')
world = conditional_import(IS_BLENDER_RUN, '.blender.world', 'world')
Light = conditional_import(IS_BLENDER_RUN, '.blender.light', 'Light')
Camera = conditional_import(IS_BLENDER_RUN, '.blender.camera', 'Camera')
annotations = conditional_import(IS_BLENDER_RUN, '.annotations')
layout = conditional_import(IS_BLENDER_RUN, '.utils.layout')
mathutils = conditional_import(IS_BLENDER_RUN, 'mathutils')
bpy = conditional_import(IS_BLENDER_RUN, 'bpy')
blender_utils = conditional_import(IS_BLENDER_RUN, '.blender.utils')

# Vanilla only imports
execute_jobs = conditional_import(not IS_BLENDER_RUN, '.run.run', 'execute_jobs')
install_module = conditional_import(not IS_BLENDER_RUN, '.utils.blender_setup.check_blender_install', 'install_module')

# Global imports
from . import file


if IS_BLENDER_RUN:
	from bpy import *  # import everything from bpy

	def load_blend(src):
		return bpy.ops.wm.open_mainfile(filepath=src)

	# set render engine to cycles
	from .run.pre_ops import on_script_open
	on_script_open()

else:
	check_blender_install(blendersynth_from_local='--local' in sys.argv)  # check install here