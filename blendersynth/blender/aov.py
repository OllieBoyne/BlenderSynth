"""Shader AOV manager"""

import bpy

ref_frames = ['CAMERA', 'WORLD', 'OBJECT']

class AOV:
	AOV_TYPE = 'COLOR'
	def __init__(self, name, **kwargs):
		self.name = name
		self._add_to_view_layer()

	def _add_to_view_layer(self, view_layer=None):
		"""Add aov to view layer if not already there"""
		if view_layer is None:
			view_layer = bpy.context.view_layer

		for aov in view_layer.aovs:
			if aov.name == self.name:
				return

		aov = view_layer.aovs.add()
		aov.name = self.name
		aov.type = self.AOV_TYPE

	def add_to_shader(self, shader_node_tree):
		"""Add AOV to shader node tree"""
		raise NotImplementedError

class NormalsAOV(AOV):
	def __init__(self, name,
					ref_frame='CAMERA',
					order='XYZ',
					polarity=(1, 1, 1)):
		"""Given a shader node tree, add surface normals as output.
		:param shader_node_tree: Shader node tree to add AOV to
		:param aov_name: Name of AOV to add
		:param ref_frame: Reference frame to use for normals
		:param order: Order of components in RGB (default: XYZ)
		:param polarity: Polarity of XYZ (1 or -1)
		"""
		super().__init__(name)
		assert ref_frame in ref_frames, f"ref_frame must be one of {ref_frames}"

		self.ref_frame = ref_frame
		self.order = order
		self.polarity = polarity

	def add_to_shader(self, shader_node_tree):

		geom_node = shader_node_tree.nodes.new('ShaderNodeNewGeometry')
		vec_transform = shader_node_tree.nodes.new('ShaderNodeVectorTransform')
		map_range_node = shader_node_tree.nodes.new('ShaderNodeMapRange')
		shader_aov_node = shader_node_tree.nodes.new('ShaderNodeOutputAOV')

		vec_transform.vector_type = 'NORMAL'
		vec_transform.convert_to = self.ref_frame

		# Set up mapping - with polarity
		map_range_node.data_type = 'FLOAT_VECTOR'
		for i in range(3):
			map_range_node.inputs[7].default_value[i] = - self.polarity[i]
			map_range_node.inputs[8].default_value[i] = self.polarity[i]

		# Set up ordering
		sep_xyz_node = shader_node_tree.nodes.new('ShaderNodeSeparateXYZ')
		comb_xyz_node = shader_node_tree.nodes.new('ShaderNodeCombineXYZ')
		for i in range(3):
			shader_node_tree.links.new(sep_xyz_node.outputs[self.order[i]], comb_xyz_node.inputs['XYZ'[i]])

		shader_aov_node.name = self.name

		# Make necessary connections for shader graph
		shader_node_tree.links.new(geom_node.outputs['True Normal'], vec_transform.inputs['Vector'])
		shader_node_tree.links.new(vec_transform.outputs['Vector'], map_range_node.inputs['Vector'])
		shader_node_tree.links.new(map_range_node.outputs['Vector'], sep_xyz_node.inputs['Vector'])
		shader_node_tree.links.new(comb_xyz_node.outputs['Vector'], shader_aov_node.inputs['Color'])