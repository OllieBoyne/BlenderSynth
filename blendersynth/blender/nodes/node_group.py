"""Custom node groups"""
import bpy
from .node_arranger import tidy_tree
import numpy as np
import os
import cv2

# docs-special-members: __init__
# no-inherited-members


class NodeGroup:
	"""Generic Node Group"""
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
	def inputs(self) -> dict:
		"""Input sockets"""
		return self.gn.inputs

	@property
	def outputs(self) -> dict:
		"""Output sockets"""
		return self.gn.outputs

	def input(self, name: str) -> bpy.types.NodeSocket:
		"""Get input socket by name"""
		return self.inputs[name]

	def output(self, name: str) -> bpy.types.NodeSocket:
		"""Get output socket by name"""
		return self.outputs[name]

	def add_node(self, key: str) -> bpy.types.Node:
		"""Create a new node in the group by name"""
		return self.group.nodes.new(key)

	def link(self, from_socket: bpy.types.NodeSocket, to_socket: bpy.types.NodeSocket) -> bpy.types.NodeLink:
		"""
		Link two sockets in the group

		:param from_socket: Socket to link from
		:param to_socket: Socket to link to
		"""
		return self.group.links.new(from_socket, to_socket)

	def __str__(self):
		return f"{self.TYPE}NodeGroup({self.name})"

	def update(self, camera=None, scene=None):
		pass

	def save_image(self, loc: str, image_data: np.ndarray):
		"""Save an image to a location. Will also reload any node reference to the image.

		:param loc: Location to save image to"""
		cv2.imwrite(loc, image_data)
		fname = os.path.basename(loc)
		if fname in bpy.data.images:
			bpy.data.images[fname].reload()

class CompositorNodeGroup(NodeGroup):
	"""Node Group for use in the compositor"""
	TYPE = 'Compositor'


class ShaderNodeGroup(NodeGroup):
	"""Node Group for use in the shader editor"""
	TYPE = 'Shader'
