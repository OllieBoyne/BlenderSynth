import appdirs
import os
import configparser
import shutil
import subprocess
import warnings

appname = "blendersynth"
appauthor = "BlenderSynth"
config_dir = appdirs.user_config_dir(appname, appauthor)
config_file = os.path.join(config_dir, "config.ini")

def is_blender_in_path():
	return shutil.which("blender") is not None

def find_blender_python(blender_path):

	if read_from_config('BLENDER_PYTHON_PATH') is not None:
		return read_from_config('BLENDER_PYTHON_PATH')

	targ_script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'blender_python_path.py'))

	# open file as read & write
	with open('___python.txt', 'w') as f:
		try:
			subprocess.check_call([blender_path, "--background", "--python",
							  targ_script], stdout=f)
		except subprocess.CalledProcessError as e:
			raise Exception(f"Issues with finding blender python path. Error: {e}")


	out = None
	with open('___python.txt', 'r') as f:
		for l in f.readlines():
			if "PYTHON INTERPRETER" in l:
				out = l.split(": ")[1].strip()
				break

	os.remove('___python.txt')

	if out is not None:
		write_to_config('BLENDER_PYTHON_PATH', out)
		return out

	raise Exception("Could not find Python interpreter for Blender.")

def validate_blender_path(blender_path):
	if os.access(blender_path, os.X_OK):
		return True

	return False

def get_blender_path(_blender_path=None):
	"""Get blender path in following order of precedence:
	1. Input arg to function
	2. In config file
	3. Environment variable BLENDER_PATH
	4. Blender in PATH
	5. Ask user for path
	"""

	cfg_result = read_from_config('BLENDER_PATH')

	if _blender_path is not None:

		if validate_blender_path(_blender_path):
			blender_path = _blender_path

		elif validate_blender_path(_blender_path + '.exe'): # add .exe if not there (helps os.access checking)
			blender_path = _blender_path + '.exe'

		else:
			raise ValueError(f"Provided Blender path, {_blender_path}, is not executable.")

	elif cfg_result is not None:
		blender_path = cfg_result

	elif os.environ.get('BLENDER_PATH') is not None:
		blender_path = os.environ.get('BLENDER_PATH')

	elif is_blender_in_path():
		blender_path = shutil.which("blender")

	else:
		blender_path = input("Blender not found in PATH or Environment Variable.\n"
							 "Please provide path to blender executable: ")

	blender_path = os.path.abspath(blender_path)  # make sure it's absolute path

	if not validate_blender_path(blender_path):
		if validate_blender_path(blender_path + '.exe'):
			blender_path += '.exe'

		else:
			raise ValueError(f"Provided Blender path, {blender_path}, is not valid as a Blender executable.")

	write_to_config('BLENDER_PATH', blender_path)
	return blender_path

def write_to_config(key, value, section='BLENDER_SETUP'):
	"""Load config, and write key value pair to cfg[section]"""
	config = configparser.ConfigParser()

	if os.path.exists(config_file):
		config.read(config_file)

	if section not in config:
		config[section] = {}

	config[section][key] = value

	with open(config_file, 'w') as configfile:
		config.write(configfile)

def read_from_config(key, section='BLENDER_SETUP'):
	"""Load config, and read value from cfg[section]"""
	config = configparser.ConfigParser()

	if os.path.exists(config_file):
		config.read(config_file)

	if section not in config:
		return None

	if key not in config[section]:
		return None

	return config[section][key]

def remove_config():
	"""Remove config file"""
	if os.path.exists(config_file):
		os.remove(config_file)
