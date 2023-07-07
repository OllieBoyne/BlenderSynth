import blendersynth as bsyn
import numpy as np
bsyn.run_this_script(debug = False)  # If called from Python, this will run the current script in Blender
# If debug set to True, this will open Blender while running

comp = bsyn.Compositor()  # Create a new compositor - this manages all the render layers

# We create a simple scene with a random selection of objects on a plane
object = bsyn.Mesh.from_primitive('monkey')

# Set some render settings
bsyn.render.set_cycles_samples(10)
bsyn.render.set_resolution(512, 512)
camera = bsyn.Camera()

comp.define_output('Image', directory='quickstart', file_name='rgb', mode='image')  # render RGB layer (note mode='image')
comp.render()  # render all the different passes - see output folder for results