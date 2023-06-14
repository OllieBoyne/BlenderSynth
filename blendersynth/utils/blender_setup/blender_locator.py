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
		return out

	raise Exception("Could not find Python interpreter for Blender.")

def validate_blender_path(blender_path):
	if os.access(blender_path, os.X_OK):
		return True

	return False

def get_blender_path(_blender_path=None):

	if _blender_path is not None:

		if validate_blender_path(_blender_path):
			blender_path = _blender_path

		elif validate_blender_path(_blender_path + '.exe'): # add .exe if not there (helps os.access checking)
			blender_path = _blender_path + '.exe'

		else:
			raise ValueError(f"Provided Blender path, {_blender_path}, is not executable.")

	elif os.environ.get('BLENDER_PATH') is not None:
		blender_path = os.environ.get('BLENDER_PATH')

	elif is_blender_in_path():
		blender_path = shutil.which("blender")

	elif load_blender_path():
		blender_path = load_blender_path()

	else:
		# raise ValueError("Blender not in PATH. Please either add to PATH or provide it to setup.py with the --blender_path argument")
		blender_path = input("Blender not found in PATH or Environment Variable.\n"
							 "Please provide path to blender executable: ")

	blender_path = os.path.abspath(blender_path) # make sure it's absolute path

	if not validate_blender_path(blender_path):
		raise ValueError(f"Provided Blender path, {blender_path}, is not valid as a Blender executable.")

	save_blender_path(blender_path)
	return blender_path

def save_blender_path(path):
	config = configparser.ConfigParser()
	config['DEFAULT'] = {'BlenderPath': path}

	os.makedirs(os.path.dirname(config_file), exist_ok=True)

	with open(config_file, 'w') as configfile:
		config.write(configfile)

def load_blender_path():
	config = configparser.ConfigParser()
	if not os.path.exists(config_file):
		warnings.warn(f"Config file not found at {config_file}. Please re-run setup.py with the --blender_path argument. (Ignore this if you are running setup.py.)")
		return None

	config.read(config_file)

	try:
		return config['DEFAULT']['BlenderPath']
	except KeyError:
		return None