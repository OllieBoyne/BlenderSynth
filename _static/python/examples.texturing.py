"""Here, we show texture importing"""

import blendersynth as bsyn
bsyn.run_this_script()

mesh = bsyn.Mesh.from_primitive('monkey')
mesh.material = bsyn.Material.from_image('../resources/monkeys/green_checkerboard.png')  # load texture
mesh.material.scale = 2  # change the scaling of the UV texture

bsyn.world.set_color((0.8, 0.7, 0.8))

bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(256, 256)

camera = bsyn.Camera()
camera.set_fov(20)  # zoom in

# render
comp = bsyn.Compositor()
comp.define_output('Image', 'texturing', file_name='rgb')
comp.render()