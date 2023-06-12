import blendersynth as bsyn
from examples.dataset_creation.generate_labels import json_dir

bsyn.execute_jobs(
	script='blender_script.py',
	json_src=json_dir,
	output_directory='example_dataset',
	num_threads=1,
)