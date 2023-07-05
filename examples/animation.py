"""Simple animation example"""
import blendersynth as bsyn
bsyn.run_this_script(debug = False)  # If called from Python, this will run the current script in Blender
# If debug set to True, this will open Blender while running

comp = bsyn.Compositor()  # Create a new compositor - this manages all the render layers

object = bsyn.Mesh.from_primitive('monkey')

# Set some render settings
bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(512, 512)
bsyn.render.set_transparent()  # Enable transparent background
num_frames = 100

# Set the 'animation' to be the rotation of the camera
camera = bsyn.Camera()
camera.track_to(object)  # look at monkey
circular_path = bsyn.Curve('circle', scale=5, location=(0, 0, 1))
camera.follow_path(circular_path, frames=(0, num_frames), fracs=(0, 0.5))  # set to follow circular path

normal_aov = bsyn.aov.NormalsAOV(ref_frame='CAMERA', polarity=[-1, 1, -1])
object.assign_aov(normal_aov)

# Define data outputs
comp.define_output('Image', directory='animation/rgb', file_name='rgb', mode='image')  # render RGB layer (note mode='image')
comp.define_output(normal_aov, directory='animation/normal', file_name='normals', mode='image')  # render RGB layer (note mode='image')

comp.render(animation=True, frame_end=num_frames)

# convert rendered frames to video
bsyn.file.frames_to_video(directory='animation/rgb', output_loc='animation/rgb.mp4', frame_rate=24, delete_images=False)
bsyn.file.frames_to_video(directory='animation/normal', output_loc='animation/normal.mp4', frame_rate=24, delete_images=False)


