"""Custom compositor node group"""
import bpy
from .node_arranger import tidy_tree


class NodeGroup:
	TYPE = 'Compositor'

	def __init__(self, name: str, node_tree: bpy.types.NodeTree):
		"""
		A generic NodeGroup class
		:param name: Name of node group
		:param node_tree: NodeTree to add group to
		"""
		self.name = name
		self.node_tree = node_tree
		self.group = bpy.data.node_groups.new(type=f'{self.TYPE}NodeTree', name=name)

		self.gn = group_node = node_tree.nodes.new(f"{self.TYPE}NodeGroup")
		group_node.node_tree = self.group

		self.input_node = self.group.nodes.new("NodeGroupInput")
		self.output_node = self.group.nodes.new("NodeGroupOutput")

	def tidy(self):
		tidy_tree(self.group)

	@property
	def inputs(self):
		return self.gn.inputs

	@property
	def outputs(self):
		return self.gn.outputs

	def input(self, name):
		return self.inputs[name]

	def output(self, name):
		return self.outputs[name]

	def add_node(self, key):
		return self.group.nodes.new(key)

	def link(self, from_socket, to_socket):
		return self.group.links.new(from_socket, to_socket)

	def __str__(self):
		return f"{self.TYPE}NodeGroup({self.name})"

	def update(self, camera=None, scene=None):
		pass


class CompositorNodeGroup(NodeGroup):
	"""Node Group for use in the compositor"""
	TYPE = 'Compositor'


class ShaderNodeGroup(NodeGroup):
	"""Node Group for use in the shader editor"""
	TYPE = 'Shader'
