import bpy
from .utils import GetNewObject, SelectObjects, handle_vec

prims = {
	'circle': bpy.ops.curve.primitive_bezier_circle_add,
	'bezier': bpy.ops.curve.primitive_bezier_curve_add,
	'path': bpy.ops.curve.primitive_nurbs_path_add,
}

class Curve:
	"""Blender path object"""
	def __init__(self, path_type='circle', scale=1, location=(0, 0, 0), rotation=(0, 0, 0)):
		"""Create a new path:

		:param path_type: Type of path to create. One of 'circle', 'bezier', 'path' (straight line)"""

		self.path = None
		self._create_path(path_type)

		self.scale = scale
		self.location = location
		self.rotation = rotation

	def _create_path(self, path_type):
		prims[path_type]()
		self.path = bpy.context.object

	@property
	def location(self):
		return self.path.location

	@location.setter
	def location(self, pos):
		self.path.location = handle_vec(pos)

	@property
	def rotation(self):
		return self.path.rotation_euler

	@rotation.setter
	def rotation(self, rot):
		self.path.rotation_euler = handle_vec(rot)

	@property
	def scale(self):
		return self.path.scale

	@scale.setter
	def scale(self, scale):
		if isinstance(scale, (int, float)):
			scale = (scale, scale, scale)

		self.path.scale = handle_vec(scale)
