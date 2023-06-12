import blendersynth as bsyn
bsyn.run_this_script(debug = False)  # If called from Python, this will run the current script in Blender

# Create a new BlenderSynth object
monkey = bsyn.BSObject.from_primitive('monkey') # Create Monkey object

# Standard render passes support
bsyn.render.render_depth()  # Enable depth pass

# AOV support - custom pass through a material shader
# Here we use this to render normals in the camera reference frame just for the monkey
cam_normals_aov = bsyn.aov.NormalsAOV('cam_normals', ref_frame='CAMERA')
monkey.assign_aov(cam_normals_aov)

bsyn.render.set_cycles_samples(100)
bsyn.render.set_resolution(512, 512)
camera = bsyn.context.scene.camera
camera.location = [0, -5, 0]
camera.rotation_euler = [3.14 / 2, 0, 0]

# create compositor to output RGB, Normals AOV & Depth
comp = bsyn.Compositor()
comp.output_to_file('Image', 'bin/rgb.png')  # render RGB layer
comp.output_to_file(cam_normals_aov.name, 'bin/normals.png')  # render normals layer
comp.output_to_file('Depth', 'bin/depth.exr', file_format='OPEN_EXR')  # render depth as EXR (as not in 0-1 range)

comp.render()