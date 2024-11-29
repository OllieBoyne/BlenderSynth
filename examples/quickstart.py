"""Script showing the basics of using BlenderSynth"""

import blendersynth as bsyn

bsyn.run_this_script(open_blender=False)  # If called from Python, this will run the current script in Blender

comp = bsyn.Compositor()  # Create a new compositor - this manages all the render layers

# Generate some basic scene components. Alternatively, use bsyn.load_blend to load a .blend file
monkey = bsyn.Mesh.from_primitive('monkey', scale=2, rotation_euler=(0, 0, 0.5))  # Create a new mesh from a primitive
light = bsyn.Light.create('POINT', location=(0, -5, 0), intensity=100)  # Create a new light

# add a basic material
monkey.material = bsyn.Material()
monkey.material.set_bdsf_property("Base Color", (0, 0.8, 0.2, 1))

# Set some render settings
bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(256, 256)
bsyn.render.set_transparent()

comp.define_output('Image', name='rgb')  # render RGB layer
comp.render().save_all('quickstart')  # render the result