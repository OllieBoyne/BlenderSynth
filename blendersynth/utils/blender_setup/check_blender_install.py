import subprocess
import os
from blendersynth.utils.blender_setup.blender_locator import find_blender_python, get_blender_path, remove_config, write_to_config, read_from_config

from time import perf_counter

dependencies = ['imageio', 'numpy', 'appdirs', 'tqdm']

def check_module(python_executable, module_name):
	try:
		subprocess.check_call([python_executable, '-m', 'pip', 'show', module_name],
							  stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
		return True
	except subprocess.CalledProcessError:
		return False

def install_module(python_executable, module_name, is_test_pypi=False,
				   version=None, upgrade=True):

	commands = [python_executable, '-m', 'pip']
	commands += ['install']
	if is_test_pypi:
		commands += ['-i', 'https://test.pypi.org/simple/']

	commands += [module_name + (f"=={version}" if version is not None else "")]
	if upgrade:
		commands += ['--upgrade']

	try:
		subprocess.check_call(commands)
	except subprocess.CalledProcessError as e:
		raise Exception(f"Could not install {module_name} via pip. Error: {e}")

def check_blender_install(force=False):
	"""Check if Blender is installed correctly and has all necessary packages.
	If not, run first time setup.

	On first time setup, will create a file, config.ini, in the user's config,
	containing the necessary info.

	Force: if True, will run first time setup (overwriting any existing config.ini)
	regardless"""

	if force:
		remove_config() # remove config file if it exists to force first time setup

	blender_path = get_blender_path()
	python_path = find_blender_python(blender_path)

	if not read_from_config('DEPENDENCIES_INSTALLED') == 'True':
		# check if blender's python has all necessary packages
		for dependency in dependencies:
			if not check_module(python_path, dependency):
				install_module(python_path, dependency)

		# Install blendersynth. For now, this is a testpypi package.
		# TODO: make this a real pypi package
		install_module(python_path, 'blendersynth', is_test_pypi=True, upgrade=True)

		write_to_config('DEPENDENCIES_INSTALLED', 'True')