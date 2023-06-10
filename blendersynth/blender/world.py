import bpy
world_nodes = bpy.data.worlds["World"].node_tree.nodes


def set_hdri(pth):
	"""Set HDRI from image path"""
	world_nodes['Environment Texture'].image = bpy.data.images.load(pth)

def set_hdri_intensity(intensity = 1.):
	world_nodes["Background"].inputs[1].default_value = intensity  # HDRI lighting