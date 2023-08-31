import bpy
from ..utils import get_node_by_name
import os
import shutil
from ..render import render, render_depth
from ..nodes import CompositorNodeGroup
from ..aov import AOV
from .mask_overlay import MaskOverlay
from .visuals import DepthVis
from .image_overlay import KeypointsOverlay, BoundingBoxOverlay, AlphaImageOverlay, AxesOverlay
from ..nodes import tidy_tree
from ..world import world


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

	def __init__(self, view_layer='ViewLayer', background_color:tuple=None,
				 rgb_color_space:str='Filmic sRGB'):
		"""
		:param view_layer: Name of View Layer to render
		:param background_color: If given, RGB[A] tuple in range [0-1], will overwrite World background with solid color (while retaining lighting effects).
		:param rgb_color_space: Color transform for RGB only.
		"""
		# Create compositor node tree
		bpy.context.scene.use_nodes = True
		self.node_tree = bpy.context.scene.node_tree
		# self.file_output_nodes = []

		self.view_layer = view_layer#

		self.file_output_nodes = {}  # Mapping of output name to FileOutputNode
		self.mask_nodes = {}  # Mapping of mask pass index to CompositorNodeGroup
		self.overlays = {}
		self.aovs = []  # List of AOVs (used to update before rendering)

		# We set view transform to 'Raw' to avoid any gamma correction to all non-Image layers
		bpy.context.scene.view_settings.view_transform = 'Raw'

		# Socket to be used as RGB input for anything. Defined separately in case of applying overlays (e.g. background colour)
		self._rgb_socket = get_node_by_name(self.node_tree, 'Render Layers').outputs['Image']
		self._set_rgb_color_space(rgb_color_space)
		if background_color is not None:
			self._set_background_color(background_color)

	def tidy_tree(self):
		"""Tidy up node tree"""
		tidy_tree(self.node_tree)

	@property
	def render_layers_node(self):
		return get_node_by_name(self.node_tree, 'Render Layers')

	def _get_render_layer_output(self, key:str):
		"""Get output socket from Render Layers node"""
		if key == 'Image': # special case
			return self._rgb_socket
		else:
			return self.render_layers_node.outputs[key]

	def get_mask(self, index, input_rgb: Union[str, CompositorNodeGroup], anti_aliasing=False) -> CompositorNodeGroup:
		"""Get mask node from pass index. If not found, create new mask node"""
		bpy.context.scene.view_layers[self.view_layer].use_pass_object_index = True  # Make sure object index is enabled

		if index not in self.mask_nodes:

			if isinstance(input_rgb, str):
				ip_node = self._get_render_layer_output(input_rgb)

			elif isinstance(input_rgb, CompositorNodeGroup):
				ip_node = input_rgb.outputs['Image']

			else:
				raise TypeError(f"input_rgb must be str or CompositorNodeGroup, got {type(input_rgb)}")

			dtype = 'Float' if isinstance(ip_node, bpy.types.NodeSocketFloat) else 'Color'

			cng = MaskOverlay(f"Mask - ID: {index} - Input {input_rgb}",
							  self.node_tree, index=index, dtype=dtype,
							  use_antialiasing=anti_aliasing)

			self.node_tree.links.new(ip_node, cng.input('Image'))
			self.node_tree.links.new(self._get_render_layer_output('IndexOB'), cng.input('IndexOB'))
			self.mask_nodes[index] = cng

		self.tidy_tree()
		return self.mask_nodes[index]

	def get_bounding_box_visual(self, col=(0., 0., 255., 255.), thickness=5) -> BoundingBoxOverlay:
		"""
		return a CompositorNodeGroup,
		which will render the bounding boxes of the objects

		:param col: (3,) or (N, 3) Color(s) of bounding box(es) [in BGR]
		:param thickness: (,) or (N,) Thickness(es) of bounding box(es)
		"""

		cng = BoundingBoxOverlay(f"Bounding Box Visual", self.node_tree, col=col, thickness=thickness)
		self.node_tree.links.new(self._get_render_layer_output('Image'), cng.input('Image'))

		if 'BBox' in self.overlays:
			raise ValueError("Only allowed one BBox overlay (it can contain multiple objects).")

		self.overlays['BBox'] = cng

		self.tidy_tree()
		return cng

	def get_keypoints_visual(self, marker:str='x', color:tuple=(0, 0, 255), size:int=5,
							 thickness:int=2) -> KeypointsOverlay:
		"""
		Initialize a keypoints overlay node.

		:param marker: Marker type, either [c/circle], [s/square], [t/triangle] or [x]. Default 'x'
		:param size: Size of marker. Default 5
		:param color: Color of marker, RGB or RGBA, default (0, 0, 255) (red)
		:param thickness: Thickness of marker. Default 2
		"""

		cng = KeypointsOverlay(f"Keypoints Visual", self.node_tree, marker=marker, color=color,
							   size=size, thickness=thickness)
		self.node_tree.links.new(self._get_render_layer_output('Image'), cng.input('Image'))

		if 'Keypoints' in self.overlays:
			raise ValueError("Only allowed one Keypoints overlay.")

		self.overlays['Keypoints'] = cng

		self.tidy_tree()
		return cng

	def get_axes_visual(self, size:int=1, thickness:int=2) -> AxesOverlay:
		"""
		Initialize an axes overlay node.

		:param size: Size of axes. Default 100
		:param thickness: Thickness of axes. Default 2
		"""

		cng = AxesOverlay(f"Axes Visual", self.node_tree,
							   size=size, thickness=thickness)
		self.node_tree.links.new(self._get_render_layer_output('Image'), cng.input('Image'))

		if 'Axes' in self.overlays:
			raise ValueError("Only allowed one Axes overlay.")

		self.overlays['Axes'] = cng
		self.tidy_tree()
		return cng

	def stack_visuals(self, *visuals: AlphaImageOverlay) -> AlphaImageOverlay:
		"""Given a series of image overlays, stack them and return to be used as a single output node.

		:param *visuals: Stack of overlays to add."""

		if len(visuals) < 2:
			raise ValueError("Requires at least 2 visuals to stack")

		# No need to store these overlays separately in self.overlays, but need to check they're all present
		for overlay in visuals:
			if overlay not in self.overlays.values():
				raise ValueError(f"Visual {overlay} not found in Compositor. Make sure it was obtained via the Compositor.")

		# Stack the output of the previous to the input of the next
		for va, vb in zip(visuals, visuals[1:]):
			self.node_tree.links.new(va.output('Image'), vb.input('Image'))

		return visuals[-1]

	def get_depth_visual(self, max_depth=1, col=(255, 255, 255)):
		"""Get depth visual, which normalizes depth values so max_depth = col,
		and any values below that are depth/max_depth * col.

		Col = 0-255 RGB or RGBA"""

		if 'Depth' not in self.render_layers_node.outputs:
			render_depth()

		# convert col to 0-1, RGBA
		col = ([i/255 for i in col] + [1])[:4]

		cng = DepthVis(self.node_tree, max_depth=max_depth, col=col)
		self.node_tree.links.new(self._get_render_layer_output('Depth'), cng.input('Depth'))

		self.tidy_tree()
		return cng

	def define_output(self, input_data: Union[str, CompositorNodeGroup, AOV], directory, file_name=None, mode='image',
					  file_format='PNG', color_mode='RGBA', jpeg_quality=90,
					  png_compression=15, color_depth='8', EXR_color_depth='32',
					  name=None):
		"""Add a connection between a valid render output, and a file output node.
		Supports changing view output.

		This should only be called once per output (NOT inside a loop).
		Inside the loop, only call `update_filename` or `update_directory`

		:mode: if 'image', export in sRGB color space. If 'data', export in raw linear color space

		:input_data: Can take one of three forms:
			- `string`, will get the input_data from that key in the render_layers_node
			- `CompositorNodeGroup`, will use that node as input
			- `AOV`, will use that AOV as input (storing AOV)

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
			self.node_tree.links.new(self._get_render_layer_output(input_data), node.inputs['Image'])

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

	def update_filename(self, key: str, fname: str):
		"""Reassign the filename (not directory) for a given file output node.

		:param key: key of output, as given in `define_output`
		:param fname: new filename, without extension"""
		fname = remove_ext(fname)
		node = self.file_output_nodes[str(key)]
		node.file_slots[0].path = fname

	def update_all_filenames(self, fname:str):
		"""Reassign all filenames (not directories) for all file output nodes.

		:param fname: new filename, without extension"""
		fname = remove_ext(fname)
		for node in self.file_output_nodes.values():
			node.file_slots[0].path = fname

	def update_directory(self, key, directory):
		"""Reassign the directory for a given file output node"""
		node = self.file_output_nodes[str(key)]
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

	def render(self, camera=None, scene=None, overlay_kwargs=None,
			   animation=False, frame_start=0, frame_end=250):
		"""Render the scene"""
		if overlay_kwargs is None:
			overlay_kwargs = {}

		if scene is None:
			scene = bpy.context.scene

		if camera is None:
			camera = scene.camera

		for k in overlay_kwargs.keys():
			assert k in self.overlays, f"overlay_kwarg {k} not in overlays: {[*self.overlays.keys()]}."

		for oname, overlay in self.overlays.items():
			args = overlay_kwargs.get(oname, {})
			if isinstance(args, dict):
				overlay.update(camera=camera, scene=scene, **args)  # multi kwargs
			else:
				overlay.update(args, camera=camera, scene=scene)  # single arg


		self.update_aovs()

		if animation:
			scene.frame_start = frame_start
			scene.frame_end = frame_end

		render(animation=animation)

		if not animation:
			self.fix_namings()

	def _set_rgb_color_space(self, color_space:str='Filmic sRGB'):
		"""Color spaces are all handled manually within compositor (so that we keep
		AOVs in raw space). So set the color space for RGB socket here."""

		color_space_node = self.node_tree.nodes.new('CompositorNodeConvertColorSpace')
		color_space_node.from_color_space = 'Linear'
		color_space_node.to_color_space = color_space

		self.node_tree.links.new(self._rgb_socket, color_space_node.inputs[0])
		self._rgb_socket = color_space_node.outputs[0]

	def _set_background_color(self, color:tuple=(0, 0, 0)):
		"""Set a solid background color, instead of transparent.
		Will remove the visuals of existing world background (but not the lighting effects).

		:param color: RGBA color, in range [0, 1]
		"""

		world.set_transparent()

		rgba = color
		if len(rgba) == 3:
			rgba = (*rgba, 1)

		rgb_node = self.node_tree.nodes.new('CompositorNodeRGB')
		rgb_node.outputs[0].default_value = rgba

		mix_node = self.node_tree.nodes.new('CompositorNodeMixRGB')

		self.node_tree.links.new(self._rgb_socket, mix_node.inputs[2])
		self.node_tree.links.new(rgb_node.outputs[0], mix_node.inputs[1])

		self.node_tree.links.new(self._get_render_layer_output('Alpha'), mix_node.inputs['Fac'])
		self._rgb_socket = mix_node.outputs['Image']