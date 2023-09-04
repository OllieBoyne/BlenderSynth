from setuptools import setup, find_packages, Extension

setup(
	name='blendersynth',
	version='0.0.5',
	install_requires=["appdirs>=1.4.4", "numpy", "tqdm", "ffmpeg-python"],
	packages=find_packages(include=['blendersynth', 'blendersynth.*']),
)