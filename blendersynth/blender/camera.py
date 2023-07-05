import bpy
import numpy as np
import mathutils
from .utils import handle_vec, SelectObjects
from typing import Union
from .mesh import Mesh
from .curve import Curve

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

	def track_to(self, obj: Union[Mesh, bpy.types.Object]):
		"""Track camera to object"""
		if isinstance(obj, Mesh):
			obj = obj.obj

		constraint = self.camera.constraints.new('TRACK_TO')
		constraint.target = obj
		constraint.track_axis = 'TRACK_NEGATIVE_Z'
		constraint.up_axis = 'UP_Y'
		self.update()

	def untrack(self):
		"""Remove track to constraint"""
		constraint = self.camera.constraints.get('Track To')
		self.camera.constraints.remove(constraint)
		self.update()

	def follow_path(self, path: Curve,	zero=True,
					animate=True, frames=(0,250), fracs=(0, 1)):
		"""Follow path, with optional animation setting.

		path: Curve object to follow
		zero: Reset camera location to 0,0,0 before following path
		"""
		constraint = self.camera.constraints.new('FOLLOW_PATH')
		constraint.target = path.path
		constraint.forward_axis = 'TRACK_NEGATIVE_Z'
		constraint.up_axis = 'UP_Y'
		constraint.use_fixed_location = True  # ensures that offset factor is in 0-1 range

		if zero:
			self.location = (0, 0, 0)

		if animate:
			self.animate_path(frames, fracs)

		# if there is are any track constraints, place this constraint first
		# so that the camera is not rotated by the track constraint
		track_constraint_idx = self.camera.constraints.find('Track To')
		if track_constraint_idx > -1:
			self.camera.constraints.move(track_constraint_idx, track_constraint_idx+1)

		self.update()

	def animate_path(self, frames=(0,250), fracs=(0, 1)):
		"""Animate camera along path.

		:param frames: tuple of keyframes to animate at - length N
		:param fracs: tuple of fractions along path to animate at - length N
		"""

		assert len(frames) == len(fracs), f"frames and fracs must be same length - got {len(frames)} and {len(fracs)}"

		for frame, frac in zip(frames, fracs):
			self.path_keyframe(frame, frac)

	def path_keyframe(self, frame, offset):
		"""Set keyframe for camera path offset

		frame: frame number
		offset: offset fraction (0-1)
		"""
		constraint = self.camera.constraints.get('Follow Path')
		if constraint is None:
			raise ValueError("Camera does not have a 'Follow Path' constraint")

		constraint.offset_factor = offset
		constraint.keyframe_insert(data_path='offset_factor', frame=frame)

		self.update()