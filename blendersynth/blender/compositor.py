import bpy
from .utils import get_node_by_name
import os
import shutil
from .render import render


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
	"""Compositor output - for handling file outputs"""
	def __init__(self):
		# Create compositor node tree
		bpy.context.scene.use_nodes = True
		self.node_tree = bpy.context.scene.node_tree
		self.file_output_nodes = []


	def output_to_file(self, name, directory, fname='_', color_management=None,
					   file_format='PNG', color_mode='RGBA', jpeg_quality=90,
					   png_compression=15, color_depth='8', EXR_color_depth='32'):
		"""Add a connection between a valid render output, and a file output node.
		Supports changing view output."""

		assert file_format in format_to_extension, f"File format `{file_format}` not supported. Options are: {list(format_to_extension.keys())}"

		node_name = f"File Output {name}"
		node = get_node_by_name(self.node_tree, node_name)

		fname = remove_ext(fname)
		directory = os.path.abspath(directory) # make sure directory is absolute
		os.makedirs(directory, exist_ok=True)

		if not node:
			# Create new 'File Output' node in compositor
			node = self.node_tree.nodes.new('CompositorNodeOutputFile')
			node.name = node_name

			# Find the output of Render Layers node by name, and link to input
			render_layers_node = get_node_by_name(self.node_tree, 'Render Layers')
			self.node_tree.links.new(render_layers_node.outputs[name], node.inputs['Image'])

			# Set file output node properties
			node.label = name
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

		return node


	def register_fname(self, key, fname):
		"""Reassign the filename (not directory) for a given file output node"""
		fname = remove_ext(fname)
		node = get_node_by_name(self.node_tree, f"File Output {key}")
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