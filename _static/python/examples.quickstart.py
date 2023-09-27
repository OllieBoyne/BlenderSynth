"""Script showing the basics of using BlenderSynth"""

import blendersynth as bsyn
bsyn.run_this_script(open_blender= False)  # If called from Python, this will run the current script in Blender
# If debug set to True, this will open Blender while running

comp = bsyn.Compositor()  # Create a new compositor - this manages all the render layers

# Generate some basic scene components. Alternatively, use bsyn.load_blend to load a .blend file
monkey = bsyn.Mesh.from_primitive('monkey', scale=2, rotation_euler=(0, 0, -0.5))  # Create a new mesh from a primitive
light = bsyn.Light.create('POINT', location=(0, -5, 0), intensity=100)  # Create a new light

# Set some render settings
bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(256, 256)
bsyn.render.set_transparent()

comp.define_output('Image', directory='quickstart', file_name='rgb')  # render RGB layer (note mode='image')
comp.render() # render the result