"""Here, we show a script that creates a dataset of monkeys with different poses - rendering RGB & Normals.
To run this script, we first generate the dataset of labels using examples/dataset_creation/generate_labels.py
Then, we run this script using create_dataset.py
"""

import blendersynth as bsyn
import sys
import os

inputs = bsyn.INPUTS()  # This is an iterable of the jsons passed in via run.py

# Create the scene
monkey = bsyn.Mesh.from_primitive('monkey')  # Create Monkey object
light = bsyn.Light.create('POINT', location=(1, 0, 0), intensity=100.)  # Create light object

# add normals AOV
cam_normals_aov = bsyn.aov.NormalsAOV('cam_normals', ref_frame='CAMERA')
monkey.assign_aov(cam_normals_aov)

bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(512, 512)

# create compositor to output RGB, Normals AOV & Depth
comp = bsyn.Compositor()
comp.define_output('Image', os.path.join('example_dataset', 'rgb'))  # render RGB layer
comp.define_output(cam_normals_aov, os.path.join('example_dataset', 'normal'))  # render normals layer

# Now iterate through and generate dataset
for i, (fname, input) in enumerate(inputs):
	# Set the pose of the monkey
	monkey.set_euler_rotation(*input['euler'])
	monkey.set_position(*input['location'])

	# Render - set the output filename to match the json filename (e.g. 0001.json -> 0001.png)
	comp.update_filename('Image', fname)
	comp.update_filename(cam_normals_aov, fname)
	# to change directory, comp.update_directory
	comp.render()

	# Save the pose and lighting as an output json
	output = {**input}  # items to save to output label
	output['bbox'] = bsyn.annotations.bounding_box(monkey, return_fmt='xywh')
	bsyn.file.save_label(output, f'example_dataset/label/{fname}.json')

	# So that the threading can track progress, log here
	bsyn.log_event(i)