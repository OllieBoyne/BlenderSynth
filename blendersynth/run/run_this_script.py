"""Quick utility to run the current script from Blender"""
import subprocess
import inspect
import sys
import os
from ..utils.blender_setup.blender_locator import get_blender_path
from ..file.tempfiles import cleanup_temp_files as cleanup

def run_this_script(debug:bool=False):
	"""Run the script in which this function is called from Blender

	:param debug: If True, open a Blender instance after all code is executed, otherwise run in background"""
	blender_path = get_blender_path()
	if blender_path != sys.argv[0]:  # if blender is not running this script

		caller_path = inspect.stack()[1].filename # path of script that called this function

		caller_dir = os.path.dirname(caller_path)
		env = os.environ.copy()
		env['PYTHONPATH'] = caller_dir + os.pathsep + env.get('PYTHONPATH', '')

		commands = [blender_path] + \
			['--background'] * (not debug) + \
			['--python', caller_path]

		subprocess.call(commands, env=env)

		cleanup()  # cleanup temp files
		sys.exit()  # exit the script once blender is finished