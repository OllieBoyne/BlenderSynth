from run_this_script import run_this_script

# Import bpy attributes, only if bpy exists
import sys

if 'blender' in sys.argv:
	from bpy import *
	from blender.object import BSObject
	from blender import render
	from blender.compositor import Compositor
	from blender import aov
	from file.dataset_inputs import INPUTS
	import file
	from run.blender_interface import log_event
	from blender import world

	# set render engine to cycles
	render.set_engine('CYCLES')

	# Clear default cube
	import bpy
	bpy.data.objects['Cube'].select_set(True)
	bpy.ops.object.delete()

else:
	# Imports for non blender
	from run.run import execute_jobs
	import file
