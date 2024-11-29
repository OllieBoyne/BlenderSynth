"""Simple animation example"""
import os

import blendersynth as bsyn
bsyn.run_this_script()

comp = bsyn.Compositor()  # Create a new compositor - this manages all the render layers

monkey = bsyn.Mesh.from_primitive('monkey')

# Set some render settings
bsyn.render.set_cycles_samples(2)
bsyn.render.set_resolution(256, 256)
num_frames = 100

# Set the 'animation' to be the rotation of the camera
camera = bsyn.Camera()
camera.track_to(monkey)  # look at monkey
circular_path = bsyn.Curve('circle', scale=5, location=(0, 0, 1))
camera.follow_path(circular_path, frames=(0, num_frames), fracs=(0, 0.5))  # set to follow circular path

light = bsyn.Light.create('POINT', location=(2, 2, 5), intensity=200)

# Also animate the position, rotation and scale of the monkey
monkey.set_location((0, 0, -2), frame=0)
monkey.set_location((0, 0, 2), frame=num_frames)
monkey.set_scale(1, frame=0)
monkey.set_scale(2, frame=num_frames)
monkey.set_rotation_euler((0, 0, 0), frame=0)
monkey.set_rotation_euler((0, 0, 3.14159/2), frame=num_frames)

# animate camera FOV
camera.set_fov(60, frame=0)
camera.set_fov(120, frame=num_frames)

normal_aov = bsyn.aov.NormalsAOV(ref_frame='CAMERA', polarity=[-1, 1, -1])
monkey.assign_aov(normal_aov)

# Define data outputs
comp.define_output('Image', name='rgb')
comp.define_output(normal_aov, name='normals')

render_result = comp.render(animation=True, frame_end=num_frames)

rgb_dir = 'animation/rgb'
normal_dir = 'animation/normal'

os.makedirs(rgb_dir, exist_ok=True)
os.makedirs(normal_dir, exist_ok=True)

for frame in range(num_frames):
    render_result.save_file(os.path.join(rgb_dir, f'rgb_{frame:03d}.png'), 'rgb', frame_number=frame)
    render_result.save_file(os.path.join(normal_dir, f'normals_{frame:03d}.png'), 'normals', frame_number=frame)

# convert rendered frames to video
bsyn.file.frames_to_video(directory='animation/rgb', output_loc='animation/rgb.gif', frame_rate=24, delete_images=False, output_fmt='gif')
bsyn.file.frames_to_video(directory='animation/normal', output_loc='animation/normal.gif', frame_rate=24, delete_images=False, output_fmt='gif')

# combine into one gif for visualisation
bsyn.file.hstack(['animation/rgb.gif', 'animation/normal.gif'], 'animation/animation_output.gif')

