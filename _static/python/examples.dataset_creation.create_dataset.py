import blendersynth as bsyn
json_dir = 'example_jsons'

bsyn.execute_jobs(
	script='blender_script.py',
	json_src=json_dir,
	output_directory='example_dataset',
	num_threads=5,
)