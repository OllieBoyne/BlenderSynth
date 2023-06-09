"""Quick utility to run the current script from Blender"""
import os, sys
import subprocess
import inspect
def run_this_script(debug=False):
	"""Run the current script from Blender"""
	if sys.argv[0] != 'blender':  # if not running in blender

		caller_path = inspect.stack()[1].filename # path of script that called this function

		commands = ['blender'] + \
			['--background'] * (not debug) + \
			['--python', caller_path]

		subprocess.call(commands)
		sys.exit() # exit the script once blender is finished