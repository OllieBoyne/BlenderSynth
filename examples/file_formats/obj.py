"""We show loading of a GLB file into a scene"""
import blendersynth as bsyn
bsyn.run_this_script(debug = True)

# Load a GLB file
mesh = bsyn.Mesh.from_obj('../../resources/monkeys/obj/monkey.obj')
mesh.rotation_euler = [3.14 / 2, 0, 0] # Rotate the mesh

bsyn.render.set_cycles_samples(10)

# render RGB and camera normals
comp = bsyn.Compositor()
cam_normals_aov = bsyn.aov.NormalsAOV('cam_normals', ref_frame='CAMERA', polarity=[-1, 1, -1])
mesh.assign_aov(cam_normals_aov)

comp.output_to_file('Image', 'obj', file_name='rgb', mode='image')
comp.output_to_file(cam_normals_aov.name, 'obj', mode='data')

comp.render()