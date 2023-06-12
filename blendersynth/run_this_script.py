"""Quick utility to run the current script from Blender"""
import os, sys
import subprocess
import inspect
import sys
from .utils.blender_locator import load_blender_path

def run_this_script(debug=False):
	"""Run the current script from Blender"""
	blender_path = load_blender_path()
	if blender_path != sys.argv[0]:  # if blender is not running this script

		caller_path = inspect.stack()[1].filename # path of script that called this function

		commands = [blender_path] + \
			['--background'] * (not debug) + \
			['--python', caller_path]

		subprocess.call(commands)
		sys.exit() # exit the script once blender is finished