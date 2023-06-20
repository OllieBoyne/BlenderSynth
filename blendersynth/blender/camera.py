import bpy
import numpy as np
import mathutils
from .utils import handle_vec

def look_at_rotation(obj_camera, at=mathutils.Vector((0, 0, 0)), up=mathutils.Vector((0, 1, 0))):
	"""	Rotate camera to look at 'at', with 'up' maintained"""

	camera_position = obj_camera.location

	z_axis = - (at - camera_position).normalized()  # Blender forwards is '-z', so use -ve here
	x_axis = up.cross(z_axis)
	y_axis = z_axis.cross(x_axis).normalized()
	is_close = all(abs(i) < 5e-3 for i in x_axis)

	if is_close:
		replacement = y_axis.cross(z_axis).normalized()
		x_axis =  replacement

	R = mathutils.Matrix([x_axis, y_axis, z_axis]).transposed()
	euler = R.to_euler()
	return euler

class Camera:
	def __init__(self, camera=None):
		if camera is None:
			camera = bpy.context.scene.camera

		self.camera = camera

	def update(self):
		bpy.context.view_layer.update()
		bpy.context.evaluated_depsgraph_get()

	@property
	def fov(self):
		"""Return FOV in degrees"""
		return self.camera.data.angle * 180/np.pi

	@property
	def location(self):
		return self.camera.location

	@location.setter
	def location(self, pos):
		self.camera.location = mathutils.Vector(pos)
		self.update()

	@property
	def euler(self):
		return self.camera.rotation_euler

	@euler.setter
	def euler(self, euler):
		self.camera.rotation_euler = euler
		self.update()

	@property
	def matrix_world(self):
		return self.camera.matrix_world

	@property
	def data(self):
		return self.camera.data


	def look_at(self, at=mathutils.Vector((0, 0, 0)), up=mathutils.Vector((0, 1, 0))):
		self.euler = look_at_rotation(self.camera, at, up)

	def place_and_rotate(self, pos, euler):
		self.location = pos
		self.euler = euler

	def place_and_look_at(self, pos, at, up=mathutils.Vector((0, 1, 0))):
		pos = handle_vec(pos)
		at = handle_vec(at)
		up = handle_vec(up)

		self.location = pos
		self.look_at(at, up)