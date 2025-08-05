"""Here, we show a script that creates a dataset of monkeys with different poses - rendering RGB & Normals.
To run this script, we first generate the dataset of labels using examples/dataset_creation/generate_labels.py
Then, we run this script using create_dataset.py
"""

import blendersynth as bsyn

# When debugging, you can use the following two lines instead of inputs = bsyn.Inputs()
# bsyn.run_this_script()
# inputs = bsyn.DebugInputs(<path to test json file>)

inputs = bsyn.Inputs()  # This is an iterable of the jsons passed in via run.py. Also manages progress bar.

# Create the scene
monkey = bsyn.Mesh.from_primitive('monkey')  # Create Monkey object
light = bsyn.Light.create('POINT', location=(1, 0, 0), intensity=100.)  # Create light object

# add normals AOV
cam_normals_aov = bsyn.aov.NormalsAOV(name='cam_normals', ref_frame='CAMERA')
monkey.assign_aov(cam_normals_aov)

bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(512, 512)

# create compositor to output RGB, Normals AOV & Depth
comp = bsyn.Compositor()
comp.define_output('Image')  # render RGB layer
comp.define_output(cam_normals_aov, name='normal')  # render normals layer

# Now iterate through and generate dataset
for i, (fname, input_data) in enumerate(inputs):
	# Set the pose of the monkey
	monkey.rotation_euler = input_data['euler']
	monkey.location = input_data['location']

	# Render - set the output filename to match the json filename (e.g. 0001.json -> 0001.png)
	# see Compositor.update_filename or Compositor.update_directory for alternative functionality
	render_result = comp.render()
	render_result.save_all(f"example_dataset/{fname}")

	# Save the pose and lighting as an output json
	output = {**input_data}  # items to save to output label
	annotation = bsyn.annotations.bounding_boxes([monkey], return_fmt='xywh').get_annotation_by_camera('Camera')
	output['bbox'] = annotation.bbox  # save the bounding box annotations
	bsyn.file.save_label(output, f'example_dataset/label/{fname}.json')