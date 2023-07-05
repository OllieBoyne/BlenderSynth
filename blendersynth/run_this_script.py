"""Quick utility to run the current script from Blender"""
import subprocess
import inspect
import sys
from .utils.blender_setup.blender_locator import get_blender_path
from .file.tempfiles import cleanup_temp_files as cleanup

def run_this_script(debug=False):
	"""Run the current script from Blender"""
	blender_path = get_blender_path()
	if blender_path != sys.argv[0]:  # if blender is not running this script

		caller_path = inspect.stack()[1].filename # path of script that called this function

		commands = [blender_path] + \
			['--background'] * (not debug) + \
			['--python', caller_path]

		subprocess.call(commands)

		cleanup()  # cleanup temp files
		sys.exit()  # exit the script once blender is finished