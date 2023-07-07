"""We show loading of a GLB file into a scene"""
import blendersynth as bsyn
bsyn.run_this_script(debug = True)

# Load a GLB file
mesh = bsyn.Mesh.from_glb('../../resources/monkeys/monkey.glb')
mesh.set_euler_rotation(3, 0, 0) # Rotate the mesh
mesh.set_position(2, 0, 0)

bsyn.render.set_cycles_samples(10)

# render RGB and camera normals
comp = bsyn.Compositor()
cam_normals_aov = bsyn.aov.NormalsAOV('cam_normals', ref_frame='CAMERA', polarity=[-1, 1, -1])
mesh.assign_aov(cam_normals_aov)

comp.define_output('Image', 'glb', file_name='rgb', mode='image')
comp.define_output(cam_normals_aov.name, 'glb', mode='data')

comp.render()