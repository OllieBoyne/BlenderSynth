"""Overlay RGB image in compositor"""
from .node_group import CompositorNodeGroup
import bpy
import cv2
import random
import string
import numpy as np
from ...file.tempfiles import create_temp_file

class AlphaImageOverlay(CompositorNodeGroup):
	"""Overlay an image on top of the render, using the alpha channel of the image as a mask"""
	def __init__(self, name='AlphaImageOverlay', node_tree=None, scene=None):
		"""Create a mix node which overlays an image on top of the input image."""

		super().__init__(name, node_tree)

		# Set default width and height
		self.width = 1000
		self.height = 1000
		if scene:
			self.width = scene.render.resolution_x
			self.height = scene.render.resolution_y

		# define I/O
		self.group.inputs.new(f'NodeSocketColor', 'Image')
		self.group.outputs.new(f'NodeSocketColor', 'Image')

		# create nodes
		self.overlay_img = self.group.nodes.new('CompositorNodeImage')
		self.mix_node = self.group.nodes.new('CompositorNodeMixRGB')
		self.sep_color_node = self.group.nodes.new('CompositorNodeSepRGBA')

		# link up internal nodes
		self.group.links.new(self.overlay_img.outputs['Image'], self.sep_color_node.inputs['Image'])

		self.group.links.new(self.input_node.outputs['Image'], self.mix_node.inputs[1])
		self.group.links.new(self.overlay_img.outputs['Image'], self.mix_node.inputs[2])
		self.group.links.new(self.sep_color_node.outputs[3], self.mix_node.inputs['Fac']) # alpha

		self.group.links.new(self.mix_node.outputs['Image'], self.output_node.inputs['Image'])

		self.create_img()

		self.tidy()

	def create_img(self):

		# create temp image to draw keypoints on, with 8 random alphanumeric characters
		# 8 random alphanum chars
		self.temp_img_loc = create_temp_file('.png')

		# initialize as white
		self.img = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
		cv2.imwrite(self.temp_img_loc, self.img)

		# connect this image to the overlay node
		self.overlay_img.image = bpy.data.images.load(self.temp_img_loc)
		return self.temp_img_loc


class KeypointsOverlay(AlphaImageOverlay):
	"""Overlay which draws keypoints on top of the render."""
	def __init__(self, name='KeypointsOverlay', node_tree=None, scene=None, camera=None):
		super().__init__(name, node_tree)

	def update(self, keypoints, scene=None, camera=None):
		"""Given [N x 3] keypoints, draw them onto a new temp image."""

		self.width = scene.render.resolution_x
		self.height = scene.render.resolution_y

		# reset image to black, with alpha = 0
		self.img = np.zeros((self.height, self.width, 4), dtype=np.uint8)

		# draw keypoints on image
		for kp in keypoints:
			cv2.circle(self.img, (int(kp[0]), int(kp[1])), 5, (0, 0, 255, 255), -1)

		cv2.imwrite(self.temp_img_loc, self.img)

class BoundingBoxOverlay(AlphaImageOverlay):
	"""Overlay which draws bounding boxes on top of the render."""
	def __init__(self, name='BoundingBoxOverlay', node_tree=None, scene=None, camera=None,
				 col=(0, 0, 255, 255), thickness=2):
		super().__init__(name, node_tree)
		self.col = col
		self.thickness = int(thickness)  # cv2 requires int

	def update(self, bboxes, scene=None, camera=None):
		"""Given [N x 4] bounding boxes, draw them onto a new temp image."""

		self.width = scene.render.resolution_x
		self.height = scene.render.resolution_y

		# reset image to black, with alpha = 0
		self.img = np.zeros((self.height, self.width, 4), dtype=np.uint8)

		col = self.col
		if len(col) == 3:
			col = (col[0], col[1], col[2], 255)

		# draw bounding boxes on image
		for bbox in bboxes:
			cv2.rectangle(self.img, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])),
						  col, self.thickness)

		cv2.imwrite(self.temp_img_loc, self.img)
