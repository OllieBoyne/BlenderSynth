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

	# open file as read & write
	with open('___python.txt', 'w') as f:
		p = subprocess.Popen([blender_path, "--background", "--python", "blendersynth/utils/blender_python_path.py"], stdout=f)
		p.wait()

	with open('___python.txt', 'r') as f:
		for l in f.readlines():
			if "PYTHON INTERPRETER" in l:
				return l.split(": ")[1].strip()

	os.remove('___python.txt')

	raise Exception("Could not find Python interpreter for Blender.")

def get_blender_path(_blender_path=None):

	if _blender_path is not None:

		if os.access(_blender_path, os.X_OK):
			blender_path = _blender_path

		elif os.access(_blender_path + '.exe', os.X_OK): # add .exe if not there (helps os.access checking)
			blender_path = _blender_path + '.exe'

		else:
			raise ValueError(f"Provided Blender path, {_blender_path}, is not executable.")

		print("Using provided blender path: ", blender_path)

	elif is_blender_in_path():
		blender_path = shutil.which("blender")
		print("Blender is in PATH: ", blender_path)

	else:
		raise ValueError("Blender not in PATH. Please either add to PATH or provide it to setup.py with the --blender_path argument")

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