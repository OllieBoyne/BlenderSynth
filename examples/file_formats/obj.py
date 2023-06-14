"""We show loading of a GLB file into a scene"""
import blendersynth as bsyn
bsyn.run_this_script(debug = False)

# Load a OBJ file
mesh = bsyn.Mesh.from_obj('../../resources/monkeys/obj/monkey.obj')
mesh.set_euler_rotation(3, 0, 0) # Rotate the mesh
mesh.set_position(2, 0, 0)

bsyn.render.set_cycles_samples(10)

# render RGB and camera normals
comp = bsyn.Compositor()
cam_normals_aov = bsyn.aov.NormalsAOV('cam_normals', ref_frame='CAMERA', polarity=[-1, 1, -1])
mesh.assign_aov(cam_normals_aov)

comp.define_output('Image', 'obj', file_name='rgb', mode='image')
comp.define_output(cam_normals_aov.name, 'obj', mode='data')

comp.render()