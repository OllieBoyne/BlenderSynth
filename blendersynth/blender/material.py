import bpy
from .bsyn_object import BsynObject
from ..utils.node_arranger import tidy_tree


def _new_shader_node(node_tree, node_type):
	shader_node = node_tree.nodes.new(type=node_type)
	if node_type == 'ShaderNodeBsdfPrincipled':
		shader_node.inputs['Specular'].default_value = 0

	return shader_node


class Material(BsynObject):
	"""BlenderSynth Material class. Will always be a node material."""

	def __init__(self, name, shader_type='ShaderNodeBsdfPrincipled', mat=None):
		if mat is None:
			mat = bpy.data.materials.new(name)
			mat.use_nodes = True
			mat.node_tree.nodes.clear()
			self.shader = _new_shader_node(mat.node_tree, shader_type)
			self.output = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
			mat.node_tree.links.new(self.shader.outputs[0], self.output.inputs['Surface'])

		mat.use_nodes = True
		self._object = mat

		self.node_tree = mat.node_tree
		self.nodes = self.node_tree.nodes
		self.links = self.node_tree.links

		# set-up scaling
		self._add_scaling_node()
		self._scale = 1

		tidy_tree(self.node_tree)


	@classmethod
	def from_image(cls, image_loc, name="ImageMaterials", shader_type='ShaderNodeBsdfPrincipled',
				   use_global_scale=True) -> 'Material':
		"""
		Create a new material from an image texture.
		:param image_loc: Location of the image
		:param name: Name of the material
		:param shader_type: Shader type
		:param use_global_scale: Flag to scale the image texture node by the global scale
		:return: New Material instance
		"""
		mat = cls(name, shader_type=shader_type)  # new instance
		mat.add_source(image_loc, input_name='Base Color', use_global_scale=use_global_scale)

		return mat

	def add_source(self, image_loc:str, input_name:str='Base Color', use_global_scale:bool=True):
		"""
		Add an image texture node to the material node tree, and connect it to the specified input of the Shader.
		:param image_loc: Image location
		:param input_name: Input socket name of the Shader to connect the image texture node to
		:param use_global_scale: Flag to scale the image texture node by the global scale
		:return:
		"""
		# Get the nodes in the material node tree
		nodes = self.obj.node_tree.nodes
		links = self.obj.node_tree.links

		# Find the Principled BSDF
		principled = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
		if not principled:
			raise ValueError("add_source requires a Principled BSDF node in the material node tree")

		# Create image texture node
		tex_image = nodes.new('ShaderNodeTexImage')
		tex_image.image = bpy.data.images.load(image_loc)

		# Connect the image texture node to the specified input of the Principled BSDF
		links.new(tex_image.outputs['Color'], principled.inputs[input_name])

		if use_global_scale:
			links.new(self._texture_scaling_socket, tex_image.inputs['Vector'])

		if 'color' not in input_name.lower():
			tex_image.image.colorspace_settings.name = 'Non-Color'

		tidy_tree(self.node_tree)

	@classmethod
	def from_blender_material(cls, blender_mat: bpy.types.Material):
		if not isinstance(blender_mat, bpy.types.Material):
			raise ValueError("Invalid Blender material")

		# Create a new Material instance
		mat = cls(blender_mat.name, mat=blender_mat)

		# Find the shader and output nodes in the copied node tree
		mat.shader = next((node for node in mat.nodes if node.type == 'BSDF_PRINCIPLED'), None)
		mat.output = next((node for node in mat.nodes if node.type == 'OUTPUT_MATERIAL'), None)

		return mat

	def _add_scaling_node(self):
		"""Add scaling node to the material node tree"""

		self.scale_node = self.nodes.new('ShaderNodeValue')
		tex_coord_node = self.nodes.new('ShaderNodeTexCoord')

		mapping_node = self.nodes.new('ShaderNodeMapping')

		self.links.new(self.scale_node.outputs[0], mapping_node.inputs['Scale'])
		self.links.new(tex_coord_node.outputs['UV'], mapping_node.inputs['Vector'])
		self._texture_scaling_socket = mapping_node.outputs['Vector']

	@property
	def scale(self):
		return self._scale

	@scale.setter
	def scale(self, value):
		self._scale = value
		self.scale_node.outputs[0].default_value = value