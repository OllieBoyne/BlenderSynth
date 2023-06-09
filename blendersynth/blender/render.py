import bpy

def render():
	bpy.ops.render.render(write_still=True)

def set_engine(engine):
	bpy.context.scene.render.engine = engine

def set_resolution(x, y):
	bpy.context.scene.render.resolution_x = x
	bpy.context.scene.render.resolution_y = y

def set_cycles_samples(samples):
	assert bpy.context.scene.render.engine == 'CYCLES', "Cycles must be the active render engine"
	bpy.context.scene.cycles.samples = samples

def render_depth():
	bpy.context.view_layer.use_pass_z = True  # enable depth pass