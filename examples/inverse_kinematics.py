import os
import blendersynth as bsyn

bsyn.run_this_script()

# Load object from .fbx file (complete with rigging)
obj = bsyn.Mesh.from_fbx('../resources/objects/bendy_rod/bendy_rod.fbx')

# render settings
bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(512, 512)
num_frames = 100

# we have a bone named 'top', which we want to control the position of
armature = obj.get_armature() # get the 'armature' - the skeleton that contains the poseable bones
bone = armature.get_bone('top')
bone_location = bone.tail_location # tail end of the bone

# here we add the constraint. We constrain the bone to `bone_location`
# We set chain_count = 4, so that the 5th bone from the end (the root bone) doesn't move
constraint = armature.add_constraint(bone, 'IK', chain_count=4)

constraint.set_location(bone_location, frame=0)
constraint.set_location(bone_location + bsyn.mathutils.Vector([2, 2, 0]), frame=num_frames//2)
constraint.set_location(bone_location, frame=num_frames)

# some small additions to make it look nice
bsyn.world.set_hdri('../resources/images/polyhaven_evening_road_01_puresky_1k.exr', intensity=0.5)  # Environment map
camera = bsyn.Camera()
camera.look_at(obj.centroid())

# now we render an animation
comp = bsyn.Compositor()
render_dir = 'inverse_kinematics/rgb'
os.makedirs(render_dir, exist_ok=True)
comp.define_output('Image', directory=render_dir, file_name='rgb')
comp.render(animation=True, frame_end=num_frames)

# convert rendered frames to video
os.makedirs(render_dir, exist_ok=True)
bsyn.file.frames_to_video(directory=render_dir, output_loc='inverse_kinematics/rgb.gif', frame_rate=24, delete_images=False, output_fmt='gif')