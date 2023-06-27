"""Custom compositor node group"""
import bpy
from ...utils.node_arranger import tidy_tree

class CompositorNodeGroup:
	def __init__(self, name, node_tree):
		self.name = name
		self.node_tree = node_tree
		self.group = bpy.data.node_groups.new(type='CompositorNodeTree', name=name)

		self.gn = group_node = node_tree.nodes.new("CompositorNodeGroup")
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

	def __str__(self):
		return f"CompositorNodeGroup({self.name})"

	def update(self, camera=None, scene=None):
		pass