import bpy
from ..utils import get_node_by_name
import os
import shutil
from ..render import render
from .node_group import CompositorNodeGroup
from ..aov import AOV
from ..mesh import Mesh
from .mask_overlay import MaskOverlay
from .shape_overlays import BBoxOverlays
from typing import Union, List
from ...utils.node_arranger import tidy_tree

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
		# self.file_output_nodes = []

		self.view_layer = view_layer#

		self.file_output_nodes = {}  # Mapping of output name to FileOutputNode
		self.mask_nodes = {}  # Mapping of mask pass index to CompositorNodeGroup
		self.overlays = {}
		self.aovs = []  # List of AOVs (used to update before rendering)

	def tidy_tree(self):
		"""Tidy up node tree"""
		tidy_tree(self.node_tree)

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

			self.node_tree.links.new(ip_node, cng.input('Image'))
			self.node_tree.links.new(self.render_layers_node.outputs['IndexOB'], cng.input('IndexOB'))
			self.mask_nodes[index] = cng

		self.tidy_tree()
		return self.mask_nodes[index]

	def get_bounding_box_visual(self, objs: Union[Mesh, List[Mesh]], col=(1., 0., 0.), thickness=0.01) -> BBoxOverlays:
		"""Given a single Mesh instance, or a list of Mesh instances, return a CompositorNodeGroup,
		which will render the bounding box of the object(s)

		:param objs: Mesh instance, or list of Mesh instances
		:param col: (3,) or (N, 3) Color(s) of bounding box(es)
		:param thickness: (,) or (N,) Thickness(es) of bounding box(es)
		"""

		if isinstance(objs, Mesh):
			objs = [objs]

		cng = BBoxOverlays(f"Bounding Box Visual - {len(objs)}", self.node_tree, objs, col=col, thickness=thickness)
		self.node_tree.links.new(self.render_layers_node.outputs['Image'], cng.input('Image'))

		if 'BBox' in self.overlays:
			raise ValueError("Only allowed one BBox overlay (it can contain multiple objects).")

		self.overlays['BBox'] = cng

		self.tidy_tree()
		return cng

	def define_output(self, input_data: Union[str, CompositorNodeGroup, AOV], directory, file_name=None, mode='image',
					  file_format='PNG', color_mode='RGBA', jpeg_quality=90,
					  png_compression=15, color_depth='8', EXR_color_depth='32',
					  name=None):
		"""Add a connection between a valid render output, and a file output node.
		Supports changing view output.

		This should only be called once per output (NOT inside a loop).
		Inside the loop, only

		:mode: if 'image', export in sRGB color space. If 'data', export in raw linear color space

		:input_node: if string, will get the input_data from that key in the render_layers_node
		:input_data: if CompositorNodeGroup, will use that node as input
		:input_data: if AOV, will use that AOV as input (storing AOV)
		:name: Name of output. If not given, will take the str representation of input_data
		"""

		if isinstance(input_data, AOV):
			self.aovs.append(input_data)
			input_data = input_data.name  # name is sufficient to pull from render_layers_node

		assert mode in ['image', 'data'], f"mode must be 'image' or 'data', got {mode}"
		assert file_format in format_to_extension, f"File format `{file_format}` not supported. Options are: {list(format_to_extension.keys())}"

		if name is None:
			name = str(input_data)

		node_name = f"File Output {name}"

		# check node doesn't exist
		if name in self.file_output_nodes:
			raise ValueError(f"File output `{name}` already exists. Only call define_output once per output type.")


		if file_name is None: # if fname is not given, use input_name
			file_name = name

		file_name = remove_ext(file_name)
		directory = os.path.abspath(directory)  # make sure directory is absolute
		os.makedirs(directory, exist_ok=True)

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

		# Set file output node properties
		node.label = node_name
		node.base_path = directory
		node.file_slots[0].path = file_name

		if mode == 'data':
			node.format.color_management = 'OVERRIDE'
			node.format.display_settings.display_device = 'None'

		# File format kwargs
		node.format.file_format = file_format
		node.format.color_mode = color_mode
		node.format.quality = jpeg_quality
		node.format.compression = png_compression
		node.format.color_depth = color_depth if file_format != 'OPEN_EXR' else EXR_color_depth

		self.file_output_nodes[name] = node

		self.tidy_tree()
		return name

	def update_filename(self, key, fname):
		"""Reassign the filename (not directory) for a given file output node"""
		fname = remove_ext(fname)
		node = self.file_output_nodes[key]
		node.file_slots[0].path = fname

	def update_directory(self, key, directory):
		"""Reassign the directory for a given file output node"""
		node = self.file_output_nodes[key]
		node.base_path = directory

	def fix_namings(self):
		"""After rendering,
		File Output node has property that frame number gets added to filename.
		Fix that here"""

		for node in self.file_output_nodes.values():
			# get expected file name and extension
			ext = format_to_extension[node.format.file_format]
			target_file_name = os.path.join(node.base_path, node.file_slots[0].path + ext)
			bad_file_name = get_badfname(target_file_name)
			shutil.move(
				bad_file_name,
				target_file_name
			)

	def update_aovs(self):
		"""Update any AOVs that are connected to the render layers node"""
		for aov in self.aovs:
			aov.update()

	def render(self):
		"""Render the scene"""
		self.update_aovs()
		render()
		self.fix_namings()
