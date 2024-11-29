import blendersynth as bsyn
import numpy as np
import os

bsyn.run_this_script()

monkey = bsyn.Mesh.from_primitive('monkey')

bsyn.render.set_resolution(256, 256)
bsyn.render.set_cycles_samples(10)

# we will create 4 cameras, one from each side of the monkey, facing the monkey
cameras = []
camera_radius = 5
for i in range(4):
	camera = bsyn.Camera.create(name=f'Cam{i}',
	location = (camera_radius * np.cos(i * np.pi / 2), camera_radius * np.sin(i * np.pi / 2), 0))
	camera.look_at_object(monkey)
	cameras.append(camera)

	# we'll add a point light at each camera too
	light = bsyn.Light.create('POINT', location=camera.location, intensity=250)

# we'll render RGB, normals, and bounding boxes
normal_aov = bsyn.aov.NormalsAOV(polarity=[-1, 1, -1])
monkey.assign_aov(normal_aov)


comp = bsyn.Compositor()
output_folder = 'multiview'
os.makedirs(output_folder, exist_ok=True)
comp.define_output('Image', name='rgb')
comp.define_output(normal_aov, name='normals')

bounding_boxes = bsyn.annotations.bounding_boxes([monkey], cameras)
comp.define_output(comp.get_bounding_box_visual(), name='bounding_box_visual')

comp.render(camera=cameras, annotations=bounding_boxes).save_all(output_folder)