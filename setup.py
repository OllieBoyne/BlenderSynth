from setuptools import setup, find_packages, Extension
import os
import subprocess
import sys
import shutil
import argparse
from blendersynth.utils.blender_locator import get_blender_path, find_blender_python

# Look for --blender_path in sys.argv, remove it if there and store blender_path
_blender_path = None
if "--blender_path" in sys.argv:
	idx = sys.argv.index("--blender_path")
	sys.argv.pop(idx)
	_blender_path = sys.argv.pop(idx)

blender_path = get_blender_path(_blender_path)
python_path = find_blender_python(blender_path) # blender's python path

# install necessary packages to blender's python
packages = ['imageio[pyav]', 'numpy', 'appdirs']
subprocess.call([python_path, "-m", "ensurepip"])
# subprocess.call([python_path, "-m", "pip", "install", "--upgrade", "pip"])
for package in packages:
	subprocess.call([python_path, "-m", "pip", "install", package])

# now can set-up from blendersynth directory

setup(
	name='blendersynth',
	version='0.1.0',
)