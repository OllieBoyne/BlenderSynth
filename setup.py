from setuptools import setup, find_packages, Extension
import os
import subprocess
import sys
import shutil

def find_blender_python(blender_path):

	# open file as read & write

	with open('___python.txt', 'w') as f:
		p = subprocess.Popen([blender_path, "--background", "--python", "blendersynth/utils/blender_python_path.py"],
										 stdout=f)

		p.wait()

	with open('___python.txt', 'r') as f:
		for l in f.readlines():
			if "PYTHON INTERPRETER" in l:
				return l.split(": ")[1].strip()

	os.remove('___python.txt')

	raise Exception("Could not find Python interpreter for Blender.")

def is_blender_in_path():
	return shutil.which("blender") is not None

def get_blender_path():
	if is_blender_in_path():
		print("Blender is in PATH.")
		blender_path = shutil.which("blender")
		print(blender_path)
	else:
		print("Blender is not in PATH.")
		blender_path = input("Enter the path to your Blender installation: ").strip()
		if not os.path.exists(blender_path):
			print("The provided path does not exist.")
			sys.exit(1)

	return blender_path

blender_path = get_blender_path()
python_path = find_blender_python(blender_path) # blender's python path

# install necessary packages to blender's python
packages = ['imageio[pyav]', 'numpy']
subprocess.call([python_path, "-m", "ensurepip"])
subprocess.call([python_path, "-m", "pip", "install", "--upgrade", "pip"])
for package in packages:
	subprocess.call([python_path, "-m", "pip", "install", package])

# now can set-up from blendersynth directory

setup(
	name='blendersynth',
	version='0.1.0',
)