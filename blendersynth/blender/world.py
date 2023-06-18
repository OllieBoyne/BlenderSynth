import bpy
from ..utils.node_arranger import tidy_tree

class World():

	def __init__(self):
		self.mode = 'Color'
		self.world = bpy.data.worlds["World"]
		self.node_tree = self.world.node_tree
		self.world_nodes = self.node_tree.nodes

		self.hdri_link = None
		self.setup_nodes()

	def setup_nodes(self):

		nodes = self.world_nodes
		nodes.clear()

		self.node_texture = nodes.new(type='ShaderNodeTexEnvironment')
		self.node_background = nodes.new(type='ShaderNodeBackground')
		self.node_output = nodes.new(type='ShaderNodeOutputWorld')

		self.node_tree.links.new(self.node_background.outputs["Background"], self.node_output.inputs["Surface"])

		tidy_tree(self.node_tree)

	def setup_color(self):
		if self.mode == 'Color':
			return

		if self.hdri_link is not None:
			self.node_tree.links.remove(self.hdri_link)

		tidy_tree(self.node_tree)

		self.mode = 'Color'

	def setup_hdri(self):
		if self.mode == 'HDRI':
			return

		# Link the nodes
		self.hdri_link = self.node_tree.links.new(self.node_texture.outputs["Color"], self.node_background.inputs["Color"])
		tidy_tree(self.node_tree)

		self.mode = 'HDRI'

	def set_color(self, color):
		self.setup_color()

		assert len(color) in [3, 4], "Color must be RGB or RGBA"

		if len(color) == 3:
			color = (*color, 1.0)

		self.node_background.inputs["Color"].default_value = color

	def set_hdri(self, pth):
		"""Set HDRI from image path"""
		self.setup_hdri()
		self.world_nodes['Environment Texture'].image = bpy.data.images.load(pth)

	def set_hdri_intensity(self, intensity = 1.):
		self.world_nodes["Background"].inputs[1].default_value = intensity  # HDRI lighting

	def set_transparent(self, transparent=True):
		bpy.context.scene.render.film_transparent = transparent

world = World()