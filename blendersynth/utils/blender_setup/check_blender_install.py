import subprocess
import os
from blendersynth.utils.blender_setup.blender_locator import find_blender_python, get_blender_path

dependencies = ['imageio', 'numpy', 'appdirs', 'tqdm']

def check_module(python_executable, module_name):
	try:
		subprocess.check_call([python_executable, '-c', f'import {module_name}'])
		return True
	except subprocess.CalledProcessError:
		return False

def install_module(python_executable, module_name):
	try:
		subprocess.check_call([python_executable, '-m', 'pip', 'install', module_name])
	except subprocess.CalledProcessError as e:
		raise Exception(f"Could not install {module_name} via pip. Error: {e}")

def check_blender_install():
	"""Check if Blender is installed correctly and has all necessary packages.
	If not, run first time setup"""

	blender_path = get_blender_path()
	python_path = find_blender_python(blender_path)

	# check if blender's python has all necessary packages
	for dependency in dependencies:
		if not check_module(python_path, dependency):
			install_module(python_path, dependency)