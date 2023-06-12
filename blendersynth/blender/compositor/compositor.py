import bpy
from ..utils import get_node_by_name
import os
import shutil
from ..render import render
from .node_group import CompositorNodeGroup
from .mask_overlay import MaskOverlay
from typing import Union

# Mapping of file formats to extensions
format_to_extension = {
	'BMP': '.bmp',
	'IRIS': '.rgb',
	'PNG': '.png',
	'JPEG': '.jpg',
	'JPEG2000': '.jp2',
	'TARGA': '.tga',
	'TARGA_RAW': '.tga',
	'CINEON': '.cin',
	'DPX': '.dpx',
	'OPEN_EXR_MULTILAYER': '.exr',
	'OPEN_EXR': '.exr',
	'HDR': '.hdr',
	'TIFF': '.tif',
	# Add more formats if needed
}


def get_badfname(fname, N=100):
	"""Search for filename in the format
	<main_fname><i:04d>.<ext>
	where i is the frame number. if no file found for i < N, raise error.
	otherwise, return found file
	"""
	f, ext = os.path.splitext(fname)
	for i in range(N):
		fname = f + f"{i:04d}" + ext
		if os.path.isfile(fname):
			return fname

	raise FileNotFoundError(f"File {fname} not found")


def remove_ext(fname):
	return os.path.splitext(fname)[0]  # remove extension if given


class Compositor:
	"""Compositor output - for handling file outputs, and managing Compositor node tree"""

	def __init__(self, view_layer='ViewLayer'):
		# Create compositor node tree
		bpy.context.scene.use_nodes = True
		self.node_tree = bpy.context.scene.node_tree
		self.file_output_nodes = []

		self.view_layer = view_layer
		self.mask_nodes = {}  # Mapping of mask pass index to CompositorNodeGroup

	@property
	def render_layers_node(self):
		return get_node_by_name(self.node_tree, 'Render Layers')

	def get_mask(self, index, input_rgb: Union[str, CompositorNodeGroup], anti_aliasing=False) -> CompositorNodeGroup:
		"""Get mask node from pass index. If not found, create new mask node"""
		bpy.context.scene.view_layers[self.view_layer].use_pass_object_index = True  # Make sure object index is enabled

		if index not in self.mask_nodes:

			if isinstance(input_rgb, str):
				ip_node = self.render_layers_node.outputs[input_rgb]

			elif isinstance(input_rgb, CompositorNodeGroup):
				ip_node = input_rgb.outputs['Image']

			else:
				raise TypeError(f"input_rgb must be str or CompositorNodeGroup, got {type(input_rgb)}")

			dtype = 'Float' if isinstance(ip_node, bpy.types.NodeSocketFloat) else 'Color'

			cng = MaskOverlay(f"Mask - ID: {index} - Input {input_rgb}",
							  self.node_tree, index=index, dtype=dtype,
							  use_antialiasing=anti_aliasing)

			self.node_tree.links.new(ip_node, cng.input('Image')) # THIS ISN'T CONNECTING CORRECTLY!!
			self.node_tree.links.new(self.render_layers_node.outputs['IndexOB'], cng.input('IndexOB'))

			# print([*self.node_tree.nodes.keys()])
			# gn = self.node_tree.nodes['Group']
			# raise ValueError(gn, cng.gn)
			# self.node_tree.links.new(self.render_layers_node.outputs['IndexOB'], gn.inputs['IndexOB'])

			self.mask_nodes[index] = cng

		return self.mask_nodes[index]

	def output_to_file(self, input_data: Union[str, CompositorNodeGroup], directory, fname='_', color_management=None,
					   file_format='PNG', color_mode='RGBA', jpeg_quality=90,
					   png_compression=15, color_depth='8', EXR_color_depth='32',
					   input_name=None):
		"""Add a connection between a valid render output, and a file output node.
		Supports changing view output.

		:input_node: if string, will get the input_data from that key in the render_layers_node
		:input_data: if CompositorNodeGroup, will use that node as input
		:input_name: Name of output. If not given, will take the str representation of input_data
		"""

		assert file_format in format_to_extension, f"File format `{file_format}` not supported. Options are: {list(format_to_extension.keys())}"

		if input_name is None:
			input_name = str(input_data)

		node_name = f"File Output {input_name}"
		node = get_node_by_name(self.node_tree, node_name)

		fname = remove_ext(fname)
		directory = os.path.abspath(directory)  # make sure directory is absolute
		os.makedirs(directory, exist_ok=True)

		if not node:
			# Create new 'File Output' node in compositor
			node = self.node_tree.nodes.new('CompositorNodeOutputFile')
			node.name = node_name

			if isinstance(input_data, str):
				self.node_tree.links.new(self.render_layers_node.outputs[input_data], node.inputs['Image'])

			elif isinstance(input_data, CompositorNodeGroup):  # add overlay in between
				self.node_tree.links.new(input_data.outputs[0], node.inputs['Image'])

			else:
				raise NotImplementedError(
					f"input_data must be either str or CompositorNodeGroup, got {type(input_data)}")

			# if mask_index is None:
			# 	self.node_tree.links.new(self.render_layers_node.outputs[input_name], node.inputs['Image'])
			#
			# else:
			# 	# Add mask node & Mix node
			# 	mask_node = self.get_mask(mask_index)
			# 	mix_node = self.node_tree.nodes.new('CompositorNodeMixRGB')
			# 	mix_node.inputs[1].default_value = (0, 0, 0, 0)  # black - 0 alpha
			#
			# 	self.node_tree.links.new(mask_node.outputs['Alpha'], mix_node.inputs['Fac'])
			# 	self.node_tree.links.new(self.render_layers_node.outputs[input_name], mix_node.inputs[2])
			# 	self.node_tree.links.new(mix_node.outputs['Image'], node.inputs['Image'])

			# Set file output node properties
			node.label = node_name
			node.base_path = directory
			node.file_slots[0].path = fname

			if color_management is not None:
				node.color_management = 'OVERRIDE'
				node.view_settings.view_transform = color_management

			# File format kwargs
			node.format.file_format = file_format
			node.format.color_mode = color_mode
			node.format.quality = jpeg_quality
			node.format.compression = png_compression
			node.format.color_depth = color_depth if file_format != 'OPEN_EXR' else EXR_color_depth

			self.file_output_nodes.append(node)

		return input_name

	def register_fname(self, key, fname):
		"""Reassign the filename (not directory) for a given file output node"""
		fname = remove_ext(fname)
		node = get_node_by_name(self.node_tree, f"File Output {str(key)}")
		node.file_slots[0].path = fname

	def fix_namings(self):
		"""After rendering,
		File Output node has property that frame number gets added to filename.
		Fix that here"""

		for node in self.file_output_nodes:
			# get expected file name and extension
			ext = format_to_extension[node.format.file_format]
			target_file_name = os.path.join(node.base_path, node.file_slots[0].path + ext)
			bad_file_name = get_badfname(target_file_name)
			shutil.move(
				bad_file_name,
				target_file_name
			)

	def render(self):
		"""Render the scene"""
		render()
		self.fix_namings()
