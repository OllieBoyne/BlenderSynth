"""Some preferential blender operations to run (e.g. setup) that will be run before debug mode is entered"""
import bpy
from ..blender import render

def on_script_open():

	render.set_engine('CYCLES')

	bpy.data.objects['Cube'].select_set(True)
	bpy.data.objects['Light'].select_set(True)
	bpy.ops.object.delete()

	bpy.context.preferences.view.show_splash = False  # disable splash screen