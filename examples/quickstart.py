import blendersynth as bsyn
bsyn.run_this_script(debug = False)  # If called from Python, this will run the current script in Blender
# If debug set to True, this will open Blender while running

comp = bsyn.Compositor()  # Create a new compositor - this manages all the render layers

# We create a simple scene of a monkey
monkey = bsyn.Mesh.from_primitive('monkey')  # Create Monkey object
monkey2 = bsyn.Mesh.from_primitive('monkey')  # Create Monkey object
monkey.location = [-0.3, 0, 0]
monkey2.location = [1.25, 0, 0]
monkey2.scale = [0.5, 0.5, 0.5]

monkey_pass_idx = monkey.assign_pass_index(1)  # Assign pass index to monkey object - used for masking
light = bsyn.Light.create('POINT', location=(1, 0, 0), intensity=100., color=(1.0, 0, 0))  # Create light object

# Set some render settings
bsyn.render.set_cycles_samples(100)
bsyn.render.set_resolution(512, 512)
camera = bsyn.Camera()
camera.location = [0, -5, 0]
camera.euler = [3.14 / 2, 0, 0]

## RENDER PASSES
# Here we show several different rendering methods
bsyn.render.render_depth()  # Enable standard Blender depth pass
rgb_mask = comp.get_mask(monkey_pass_idx, 'Image')  # create an RGB mask (i.e. only render monkey)
bounding_box_visual = comp.get_bounding_box_visual([monkey, monkey2], col=((1,0,0),(0,1,0)))  # create a bounding box visual
bounding_box_visual.update(camera)

# AOV support - custom pass through a material shader
# Here we use this to render normals in the camera reference frame just for the monkey
cam_normals_aov = bsyn.aov.NormalsAOV('cam_normals', ref_frame='CAMERA', polarity=[-1, 1, -1])
monkey.assign_aov(cam_normals_aov) # Have to assign this to any object that uses this AOV


# Now we assign our render passes to the compositor, telling it what files to output
output_folder = 'quickstart'
comp.output_to_file('Image', output_folder, file_name='rgb')  # render RGB layer
comp.output_to_file(cam_normals_aov.name, output_folder)  # render normals layer
comp.output_to_file(rgb_mask, output_folder, input_name='rgb_masked') # render RGB layer masked by monkey
comp.output_to_file('Depth', output_folder, file_format='OPEN_EXR')  # render depth as EXR (as not in 0-1 range)
comp.output_to_file(bounding_box_visual, output_folder, input_name='bounding_box_visual')

comp.render()  # render all the different passes - see output folder for results