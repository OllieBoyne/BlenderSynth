import bpy
import numpy as np
import mathutils

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

	@property
	def fov(self):
		"""Return FOV in degrees"""
		return self.camera.data.angle * 180/np.pi

	@property
	def position(self):
		return self.camera.location

	@position.setter
	def position(self, pos):
		self.camera.location = mathutils.Vector(pos)
		bpy.context.evaluated_depsgraph_get()  # need to update despgraph to update camera position
	@property
	def euler(self):
		return self.camera.rotation_euler

	@euler.setter
	def euler(self, euler):
		self.camera.rotation_euler = euler
		bpy.context.evaluated_depsgraph_get()  # need to update despgraph to update camera position

	def look_at(self, at=mathutils.Vector((0, 0, 0)), up=mathutils.Vector((0, 1, 0))):
		self.euler = look_at_rotation(self.camera, at, up)

	def place_and_rotate(self, pos, euler):
		self.position = pos
		self.euler = euler

	def place_and_look_at(self, pos, at, up=mathutils.Vector((0, 1, 0))):
		self.position = pos
		self.look_at(at, up)