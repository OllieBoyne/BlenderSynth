import blendersynth as bsyn
import numpy as np

bsyn.run_this_script(open_blender=False)

comp = bsyn.Compositor() # Create a new compositor - this manages all the render layers

# We create a simple scene with a random selection of objects on a plane
floor = bsyn.Mesh.from_primitive('plane', scale=35) # Create floor
N = 10 # Number of objects
R = 3 # Radius of circle
np.random.seed(6)
objects = []
for i in range(N):
	object = bsyn.Mesh.from_primitive(['monkey', 'cone', 'sphere', 'cube'][np.random.randint(4)],
							 scale=np.random.uniform(0.3, 1.0),
							 location=(np.sin(i / N * 2 * np.pi) * R, np.cos(i / N * 2 * np.pi) * R, 0) # place in a circle
									  )
	object.set_minimum_to('Z', 0)
	objects.append(object)

obj_pass_idx = objects[0].assign_pass_index(1)  # To show masking, we assign a pass index to the first object

# add some lights
point_light = bsyn.Light.create('POINT', location=(0, 0, 6), intensity=1000.)
sun_light = bsyn.Light.create('SUN')

# Set some render settings
bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(512, 512)
camera = bsyn.Camera()

## RENDER PASSES
# Here we show several different rendering methods
bsyn.render.render_depth()  # Enable standard Blender depth pass
depth_vis = comp.get_depth_visual(max_depth=20)  # Create a visual of the depth pass
rgb_mask = comp.get_mask(obj_pass_idx, 'Image')  # create an RGB mask (i.e. only render monkey)
bounding_box_visual = comp.get_bounding_box_visual()
keypoints_visual = comp.get_keypoints_visual()  # Create a visual of keypoints
axes_visual = comp.get_axes_visual()  # Create a visual of axes

# AOV support - custom pass through a material shader
# For simplicity, we will assign all AOVs to all objects - but that doesn't have to be done.
all_objects = objects + [floor]

cam_normals_aov = bsyn.aov.NormalsAOV(ref_frame='CAMERA', polarity=[-1, 1, -1])
binary_mask_aov = bsyn.aov.ValueAOV(value=1)
instancing_aov = bsyn.aov.InstanceRGBAOV()
class_aov = bsyn.aov.ClassRGBAOV()
UVAOV = bsyn.aov.UVAOV()  # UV Coordinates
NOCAOV = bsyn.aov.GeneratedAOV()  # Normalized Object Coordinates (NOC)

for aov in [cam_normals_aov, instancing_aov, class_aov, UVAOV, NOCAOV]:
	for obj in all_objects:
		obj.assign_aov(aov)

for obj in all_objects:
	if 'Cube' in obj.name:
		obj.assign_aov(binary_mask_aov)

# Now we assign our render passes to the compositor, telling it what files to output
output_folder = 'data_formats'

# All of the following will have Blender's Filmic/AgX (<4.0, >4.0) colour correction by default
comp.define_output('Image', name='rgb')  # render RGB layer
comp.define_output(rgb_mask, name='rgb_masked') # render RGB layer masked by monkey
comp.define_output(bounding_box_visual, name='bounding_box_visual')
comp.define_output(keypoints_visual, name='keypoints')
comp.define_output(axes_visual, name='axes')

# All of the following will not have any colour correction
comp.define_output(depth_vis, is_data=True)  # render visual of depth layer
comp.define_output(binary_mask_aov, name='binary_mask', is_data=True)
comp.define_output(instancing_aov, name='instancing', is_data=True)
comp.define_output(class_aov, name='semantic', is_data=True)
comp.define_output(cam_normals_aov, name='normals', is_data=True)
comp.define_output(UVAOV, name='UV', is_data=True)
comp.define_output(NOCAOV, name='NOC', is_data=True)
comp.define_output('Depth', file_format='OPEN_EXR', is_data=True)

# we will plot all cube keypoints
cube_vertices = np.concatenate([obj.get_keypoints([*range(8)]) for obj in objects if 'Cube' in obj.name])
keypoints = bsyn.annotations.keypoints.project_keypoints(cube_vertices)

# and all bounding boxes
bounding_boxes = bsyn.annotations.bounding_boxes(objects, camera)

# and all axes
axes = bsyn.annotations.get_axes(objects)

render_result = comp.render(camera=camera, annotations=keypoints + bounding_boxes + axes)  # render all the different passes - see output folder for results
render_result.save_all(output_folder)