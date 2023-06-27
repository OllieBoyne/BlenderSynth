import tempfile
import os

tempdir = os.path.join(tempfile._get_default_tempdir(), 'blendersynth')
os.makedirs(tempdir, exist_ok=True)

def create_temp_file(ext='.png'):
	"""Create temporary filename, return filename"""
	return tempfile.mktemp(dir = tempdir) + ext

def cleanup_temp_files():
	"""Get list of all temporary files, delete them"""
	for f in os.listdir(tempdir):
		os.remove(os.path.join(tempdir, f))