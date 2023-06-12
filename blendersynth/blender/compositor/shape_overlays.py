"""Use compositor nodes to draw shape overlays on rendered images"""
from .node_group import CompositorNodeGroup

class RectangleOverlay(CompositorNodeGroup):
	def __init__(self, node_tree, x, y, w, h, col=(1.0, 0.0, 0.0), thickness=0.1):
		super().__init__("Rectangle Overlay", node_tree)

		# create nodes
		self.box_mask_1 = self.node_tree.nodes.new('CompositorNodeBoxMask')
		self.box_mask_2 = self.node_tree.nodes.new('CompositorNodeBoxMask')
		self.subtract = self.node_tree.nodes.new('CompositorNodeMath')
		self.subtract.operation = 'SUBTRACT'
		self.mix_node = self.node_tree.nodes.new('CompositorNodeMixRGB')

		self._x = x
		self._y = y
		self._w = w
		self._h = h
		self._thickness = thickness
		self.update_box_masks()

		self.col = col

	def update_box_masks(self):
		self.box_mask_1.X = self.x
		self.box_mask_1.Y = self.y
		self.box_mask_1.Width = self.w
		self.box_mask_1.Height = self.thickness

		self.box_mask_2.X = self.x
		self.box_mask_2.Y = self.y
		self.box_mask_2.Width = self.w - 2 * self.thickness
		self.box_mask_2.Height = self.h - 2 * self.thickness


	@property
	def x(self):
		return self._x

	@x.setter
	def x(self, x):
		self._x = x
		self.update_box_masks()

	@property
	def y(self):
		return self._y

	@y.setter
	def y(self, y):
		self._y = y
		self.update_box_masks()

	@property
	def w(self):
		return self._w

	@w.setter
	def w(self, w):
		self._w = w
		self.update_box_masks()

	@property
	def h(self):
		return self._h

	@h.setter
	def h(self, h):
		self._h = h
		self.update_box_masks()

	@property
	def col(self):
		return self._col

	@col.setter
	def col(self, col):
		self._col = col
		self.mix_node.color1 = col

	@property
	def thickness(self):
		return self._thickness

	@thickness.setter
	def thickness(self, thickness):
		self._thickness = thickness
		self.update_box_masks()
