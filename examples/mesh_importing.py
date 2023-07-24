"""In this example, we will import a mesh from a .obj file and render it with a material."""

import blendersynth as bsyn
bsyn.run_this_script(debug = False)

# Load a OBJ file
mesh = bsyn.Mesh.from_obj('../resources/monkeys/obj/monkey.obj')
bsyn.world.set_color((0.8, 0.7, 0.8))

bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(256, 256)

camera = bsyn.Camera()
camera.set_fov(20)  # zoom in

# render
comp = bsyn.Compositor()
comp.define_output('Image', 'obj', file_name='rgb', mode='image')
comp.render()