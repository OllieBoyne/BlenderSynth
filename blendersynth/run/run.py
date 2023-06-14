import os

from .blender_threading import BlenderThreadManager, list_split
from ..utils.blender_setup.blender_locator import get_blender_path

from sys import platform
if platform == "linux" or platform == "linux2" or platform == "darwin":
	nul_text = '/dev/null'
elif platform == "win32":
	nul_text = 'nul'



class BlenderCommand:
	"""Construct command for running blender script"""
	def __init__(self, blender_loc, background=True):
		self.base_command = [blender_loc, "--background" if background else ""]
		self._command = self.base_command

	def compose(self, script, silent, args=(), **kwargs):
		command = self.base_command + ["--python", script]
		command += [f"1> {nul_text}" if silent else "", "--"]
		for arg in args:
			command.append(f"--{arg}")

		for k, v in kwargs.items():
			command += [f"--{k}", str(v)]

		self._command = command

	@property
	def command(self):
		return self._command

	def set_job(self, job_list):
		"""Receives list of json files, adds as , separated string to command"""
		return self._command + ["--jobs", ",".join(job_list)]

class Runner:
	def __init__(self, script, jsons, output_directory, num_threads=1,
				 print_to_stdout=False,
				 **script_kwargs):
		"""
		:param jsons: N sized list of .json files, each with info about the given job
		:param num_threads: threads to run in parallel (default = 1)
		"""
		self.jsons = jsons
		self.num_threads = num_threads

		# Split the jsons into num_threads chunks
		json_chunks = list_split(self.jsons, self.num_threads)

		blender_loc = get_blender_path()
		command = BlenderCommand(blender_loc=blender_loc, background=True)
		command.compose(script=script, silent=True, **script_kwargs)

		thread_manager = BlenderThreadManager(command, json_chunks, print_to_stdout=print_to_stdout,
											  output_directory=output_directory)

		thread_manager.start()

def execute_jobs(script, json_src, output_directory, num_threads=1,
				 print_to_stdout=False, **script_kwargs):
	"""
	:param json_src: N sized list of .json files, each with info about the given job. OR a directory containing .json files,
		which will be used as the jsons
	:param num_threads: threads to run in parallel (default = 1)
	"""

	assert not(num_threads> 1 and print_to_stdout), "Cannot print to stdout with multiple threads"
	if print_to_stdout:
		raise NotImplementedError("Print to stdout not supported yet.")

	if isinstance(json_src, str):
		json_src = sorted([os.path.join(json_src, f) for f in os.listdir(json_src) if f.endswith(".json")])

	Runner(script, json_src, output_directory, num_threads, print_to_stdout=print_to_stdout,
			**script_kwargs)