import blendersynth as bsyn
bsyn.run_this_script(debug = False)  # If called from Python, this will run the current script in Blender

comp = bsyn.Compositor()  # Create a new compositor - this manages all the render layers

# Create a new BlenderSynth object
monkey = bsyn.Mesh.from_primitive('monkey')  # Create Monkey object
monkey_pass_idx = monkey.assign_pass_index(1)  # Assign pass index to monkey object - used for masking
light = bsyn.Light.create('POINT', location=(1, 0, 0), intensity=100., color=(1.0, 0, 0))  # Create light object

# Standard render passes support
bsyn.render.render_depth()  # Enable depth pass

# Masking support (can be used for any render pass, here we use for RGB)
rgb_mask = comp.get_mask(monkey_pass_idx, 'Image')  # create a depth mask

# AOV support - custom pass through a material shader
# Here we use this to render normals in the camera reference frame just for the monkey
cam_normals_aov = bsyn.aov.NormalsAOV('cam_normals', ref_frame='CAMERA', polarity=[-1, 1, -1])
monkey.assign_aov(cam_normals_aov)


bsyn.render.set_cycles_samples(100)
bsyn.render.set_resolution(512, 512)
camera = bsyn.context.scene.camera
camera.location = [0, -5, 0]
camera.rotation_euler = [3.14 / 2, 0, 0]

# create compositor to output RGB, Normals AOV & Depth

output_folder = 'quickstart'
comp.output_to_file('Image', output_folder)  # render RGB layer
comp.output_to_file(cam_normals_aov.name, output_folder)  # render normals layer
comp.output_to_file(rgb_mask, output_folder, input_name='rgb_masked') # render RGB layer masked by monkey

# We render depth for whole image
comp.output_to_file('Depth', output_folder, file_format='OPEN_EXR')  # render depth as EXR (as not in 0-1 range)


# have to register filenames separately (used for large scale dataset creation)
comp.register_fname('Image', 'rgb')
comp.register_fname(cam_normals_aov.name, 'normals')
comp.register_fname('Depth', 'depth')
comp.register_fname('rgb_masked', 'rgb_masked')

comp.render()