"""Shader AOV manager"""

import bpy
from ..utils.node_arranger import tidy_tree

ref_frames = ['CAMERA', 'WORLD', 'OBJECT']

class AOV:
	AOV_TYPE = 'COLOR'
	def __init__(self, name=None, **kwargs):
		if name is None:
			name = self.__class__.__name__

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
		self._add_to_shader(shader_node_tree)
		tidy_tree(shader_node_tree)

	def _add_to_shader(self, shader_node_tree):
		raise NotImplementedError

	def update(self):
		"""Some AOVs need an update before rendering (to change certain node properties)"""
		return

class NormalsAOV(AOV):
	def __init__(self, name=None,
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

	def _add_to_shader(self, shader_node_tree):

		geom_node = shader_node_tree.nodes.new('ShaderNodeNewGeometry')
		vec_transform = shader_node_tree.nodes.new('ShaderNodeVectorTransform')
		map_range_node = shader_node_tree.nodes.new('ShaderNodeMapRange')
		shader_aov_node = shader_node_tree.nodes.new('ShaderNodeOutputAOV')
		shader_aov_node.name = self.name

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

		# Make necessary connections for shader graph
		shader_node_tree.links.new(geom_node.outputs['True Normal'], vec_transform.inputs['Vector'])
		shader_node_tree.links.new(vec_transform.outputs['Vector'], map_range_node.inputs['Vector'])
		shader_node_tree.links.new(map_range_node.outputs['Vector'], sep_xyz_node.inputs['Vector'])
		shader_node_tree.links.new(comb_xyz_node.outputs['Vector'], shader_aov_node.inputs['Color'])

	def update(self, scene=None):
		"""Some AOVs may need render_time updates from scene context, hence this method"""
		pass

class NOCAOV(AOV):
	"""Normalised object coordinates - Gives the position of the object in object space,
	normalised to the object's bounding box."""

	def _add_to_shader(self, shader_node_tree):
		texcon_node = shader_node_tree.nodes.new('ShaderNodeTexCoord')
		shader_aov_node = shader_node_tree.nodes.new('ShaderNodeOutputAOV')
		shader_aov_node.name = self.name

		shader_node_tree.links.new(texcon_node.outputs['Generated'], shader_aov_node.inputs['Color'])


class UVAOV(AOV):
	"""UV coordinates"""

	def _add_to_shader(self, shader_node_tree):
		texcon_node = shader_node_tree.nodes.new('ShaderNodeTexCoord')
		shader_aov_node = shader_node_tree.nodes.new('ShaderNodeOutputAOV')
		shader_aov_node.name = self.name

		shader_node_tree.links.new(texcon_node.outputs['UV'], shader_aov_node.inputs['Color'])


class AttrAOV(AOV):
	"""Take an object attribute, and output it as an AOV"""
	attribute_type = None
	attribute_name = None

	def _add_to_shader(self, shader_node_tree):
		attr_node = shader_node_tree.nodes.new('ShaderNodeAttribute')
		attr_node.attribute_type = self.attribute_type
		attr_node.attribute_name = self.attribute_name

		shader_aov_node = shader_node_tree.nodes.new('ShaderNodeOutputAOV')
		shader_aov_node.name = self.name

		shader_node_tree.links.new(attr_node.outputs['Instance Index'], shader_aov_node.inputs['Value'])

class InstanceIDAOV(AttrAOV):
	"""Instance ID - given to each object on creation.
	Output is an integer corresponding to the object's instance ID (0-indexed)
	"""
	attribute_type = 'OBJECT'
	attribute_name = 'instance_id'

class ClassIDAOV(AttrAOV):
	"""Class ID - given to each object on creation.
	Output is an integer corresponding to the object's class ID (0-indexed)
	Class IDs can be manually set either when creating a Mesh, or by using the Mesh's set_class_id() method.
	If not set, will default to a different index from each primitive.
	"""
	attribute_type = 'OBJECT'
	attribute_name = 'class_id'

class AttrRGBAOV(AOV):
	"""
	For a given numerical attribute, outputs a color corresponding to the attribute's value.
	For N objects total, samples evenly on a distribution of hues, on a colour scale of S = 1, V = 1
	Runs update() method to change the value of N, which is called before rendering.
	N can be a property of the object to update.
	"""
	attribute_type = None
	attribute_name = None

	def __init__(self, name=None):
		super().__init__(name)

		# Create Int Index -> HSV as a node group, so the 'num_objects' parameter can be edited centrally
		self.group = bpy.data.node_groups.new(name='IdxToHue', type='ShaderNodeTree')

		self.group.inputs.new(f'NodeSocketInt', 'Index')
		self.group.outputs.new(f'NodeSocketColor', 'Color')

		self.input_node = self.group.nodes.new('NodeGroupInput')
		self.output_node = self.group.nodes.new('NodeGroupOutput')

		self.div_node = div_node = self.group.nodes.new('ShaderNodeMath')  # Need to keep reference so can update at runtime
		div_node.operation = 'DIVIDE'
		div_node.use_clamp = True
		div_node.inputs[1].default_value = self.N

		hsv_node = self.group.nodes.new('ShaderNodeHueSaturation')
		hsv_node.inputs['Saturation'].default_value = 1
		hsv_node.inputs['Value'].default_value = 1
		hsv_node.inputs['Color'].default_value = (1, 0, 0, 1) # Red

		self.group.links.new(self.input_node.outputs['Index'], div_node.inputs[0])
		self.group.links.new(div_node.outputs['Value'], hsv_node.inputs['Hue'])
		self.group.links.new(hsv_node.outputs['Color'], self.output_node.inputs['Color'])
		tidy_tree(self.group)

	def _add_to_shader(self, shader_node_tree):
		attr_node = shader_node_tree.nodes.new('ShaderNodeAttribute')
		attr_node.attribute_type = self.attribute_type
		attr_node.attribute_name = self.attribute_name

		# Create a group node for the Int Index -> HSV conversion
		group_node = shader_node_tree.nodes.new('ShaderNodeGroup')
		group_node.node_tree = self.group

		shader_aov_node = shader_node_tree.nodes.new('ShaderNodeOutputAOV')
		shader_aov_node.name = self.name

		shader_node_tree.links.new(attr_node.outputs['Fac'], group_node.inputs['Index'])
		shader_node_tree.links.new(group_node.outputs['Color'], shader_aov_node.inputs['Color'])

	def update(self):
		self.div_node.inputs[1].default_value = self.N

	@property
	def N(self):
		return 0

class InstanceRGBAOV(AttrRGBAOV):
	"""
	Similar to InstanceIDAOV, but outputs an RGB value corresponding to the object's instance ID.
	For N instances total, samples evenly on a distribution of hues, on a colour scale of S = 1, V = 1.
	Updates N at render time by reading the scene property 'NUM_MESHES'
	"""
	attribute_type = 'OBJECT'
	attribute_name = 'instance_id'

	@property
	def N(self):
		"""Update the divisor node with the current number of instances"""
		return bpy.context.scene.get('NUM_MESHES', 0) + 1

class ClassRGBAOV(AttrRGBAOV):
	"""
	Similar to ClassIDAOV, but outputs an RGB value corresponding to the object's class ID.
	For N classes total, samples evenly on a distribution of hues, on a colour scale of S = 1, V = 1.
	Updates N at render time by reading the scene property 'MAX_CLASSES'
	"""
	attribute_type = 'OBJECT'
	attribute_name = 'class_id'

	@property
	def N(self):
		"""Update the divisor node with the current number of classes"""
		return bpy.context.scene.get('MAX_CLASSES', 0) + 1