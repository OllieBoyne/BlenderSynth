"""Use compositor nodes to draw shape overlays on rendered images"""
from .node_group import CompositorNodeGroup
from ...annotations.bbox import bounding_box

class RectangleOverlay(CompositorNodeGroup):
	def __init__(self, node_tree, col=(1.0, 0.0, 0.0), thickness=0.01):
		super().__init__('RectangleOverlay', node_tree)

		self.group.outputs.new(f'NodeSocketColor', 'Image')
		self.group.outputs.new(f'NodeSocketFloat', 'Mask')

		self.box_mask_outer = self.group.nodes.new('CompositorNodeBoxMask')
		self.box_mask_inner = self.group.nodes.new('CompositorNodeBoxMask')
		self.subtract = self.group.nodes.new('CompositorNodeMath')
		self.subtract.operation = 'SUBTRACT'

		self.gt = self.group.nodes.new('CompositorNodeMath')
		self.gt.operation = 'GREATER_THAN'
		self.gt.inputs[1].default_value = 0.0
		self.gt.use_clamp = True

		self.rgb = self.group.nodes.new('CompositorNodeRGB')
		self.rgb.outputs[0].default_value = col + (1.0,)

		self.set_alpha = self.group.nodes.new('CompositorNodeSetAlpha')
		self.set_alpha.mode = 'APPLY'

		self.group.links.new(self.box_mask_outer.outputs['Mask'], self.subtract.inputs[0])
		self.group.links.new(self.box_mask_inner.outputs['Mask'], self.subtract.inputs[1])
		self.group.links.new(self.subtract.outputs['Value'], self.gt.inputs[0])
		self.group.links.new(self.gt.outputs['Value'], self.set_alpha.inputs['Alpha'])
		self.group.links.new(self.rgb.outputs['RGBA'], self.set_alpha.inputs['Image'])
		self.group.links.new(self.set_alpha.outputs['Image'], self.output_node.inputs['Image'])
		self.group.links.new(self.gt.outputs['Value'], self.output_node.inputs['Mask'])


		self._thickness = thickness
		self.col = col
		self.tidy()

	def set_dimensions(self, x0, y0, w, h):
		"""Given dimensions in format
		(x0, y0, w, h), (x0, y0) is bottom left corner"""
		self.box_mask_outer.x = x0 + w / 2
		self.box_mask_outer.y = y0 + h / 2
		self.box_mask_outer.width = w
		self.box_mask_outer.height = h

		self.box_mask_inner.x = x0 + w / 2
		self.box_mask_inner.y = y0 + h / 2
		self.box_mask_inner.width = w - 2 * self.thickness
		self.box_mask_inner.height = h - 2 * self.thickness

	@property
	def thickness(self):
		return self._thickness


	@thickness.setter
	def thickness(self, value):
		self._thickness = value
		self.set_dimensions(self.box_mask_outer.x, self.box_mask_outer.y, self.box_mask_outer.width, self.box_mask_outer.height)


class BBoxOverlays(CompositorNodeGroup):
	"""Creates N Rectangle overlay visuals"""
	def __init__(self, name, node_tree, objs, col=(1.0, 0.0, 0.0), thickness=0.01):
		"""Create N bounding boxes
		x: (N,) array of x coordinates
		y: (N,) array of y coordinates
		w: (N,) array of widths
		h: (N,) array of heights
		col: (N, 3) or (3,) array of colors
		thickness: (N,) or (1,) array of thicknesses

		Will draw in order of list.

		"""
		super().__init__(name, node_tree)

		self.objs = objs
		N = len(objs)

		self.group.inputs.new(f'NodeSocketColor', 'Image')
		self.group.outputs.new(f'NodeSocketColor', 'Image')

		if isinstance(col[0], float): col = [col] * N
		if isinstance(thickness, float): thickness = [thickness] * N

		last_image = None
		last_mask = None
		self.rect_overlays = []

		# Create sub node group for each rectangle which outputs an image.
		# Use MixNodes to collect the rectangle overlays as we go along
		# Use AddNodes to collect the masks as we go along
		for n in range(N):
			rectangle_overlay = RectangleOverlay(self.group, col[n], thickness[n])
			self.rect_overlays.append(rectangle_overlay)

			# We need to mix together all N input nodes (using Add Mixers).
			if last_image is None:
				last_image = rectangle_overlay.outputs['Image']
				last_mask = rectangle_overlay.outputs['Mask']


			else:
				mix_node = self.group.nodes.new('CompositorNodeMixRGB')
				mix_node.use_clamp = True
				self.group.links.new(last_mask, mix_node.inputs[0])
				self.group.links.new(rectangle_overlay.outputs['Image'], mix_node.inputs[1])
				self.group.links.new(last_image, mix_node.inputs[2])

				add_node = self.group.nodes.new('CompositorNodeMath')
				add_node.operation = 'ADD'
				add_node.use_clamp = True
				self.group.links.new(last_mask, add_node.inputs[0])
				self.group.links.new(rectangle_overlay.outputs['Mask'], add_node.inputs[1])

				last_image = mix_node.outputs['Image']
				last_mask = add_node.outputs['Value']

		# Now combine this with input image
		self.final_mix_node = self.group.nodes.new('CompositorNodeMixRGB')
		self.final_mix_node.use_clamp = True

		self.group.links.new(last_mask, self.final_mix_node.inputs[0])
		self.group.links.new(self.input_node.outputs['Image'], self.final_mix_node.inputs[1])
		self.group.links.new(last_image, self.final_mix_node.inputs[2])


		self.group.links.new(self.final_mix_node.outputs['Image'], self.output_node.inputs['Image'])


		self.tidy()

	def update_box_mask(self, x, y, w, h, i=0):
		self.rect_overlays[i].set_dimensions(x, y, w, h)

	def update(self, camera = None, scene = None):
		for n, obj in enumerate(self.objs):
			x, y, w, h = bounding_box(obj, camera, scene, return_fmt='xywh', normalized=True, invert_y=False)
			self.update_box_mask(x, y, w, h, n)

