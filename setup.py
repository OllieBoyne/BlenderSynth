from setuptools import setup, find_packages, Extension

setup(
	name='blendersynth',
	version='0.2.0',
	install_requires=["platformdirs>=3.11.0", "numpy", "tqdm", "ffmpeg-python"],
	packages=find_packages(include=['blendersynth', 'blendersynth.*']),
)