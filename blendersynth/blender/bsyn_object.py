"""Base class for all BlenderSynth objects."""
from .utils import handle_vec, SelectObjects, _euler_add, _euler_from, animatable_property
from mathutils import Vector, Euler
import numpy as np
import bpy
from typing import Union
from ..utils import types

class BsynObject:
	"""Generic class for BlenderSynth objects."""
	_object = None # corresponding blender object

	@property
	def obj(self):
		if self._object is None:
			raise ValueError("self._object not set. Ensure it is set in the Object's __init__ function.")

		return self._object

	@property
	def object(self):
		return self.obj

	@property
	def data(self):
		return self.object.data

	# def update(self):
	#   ---> not currently needed, may be needed in the future
	# 	"""On any update, run this. For most objects, this is a no-op, but for some objects,
	# 	this is necessary to update the object's state. e.g. Camera"""
	# 	return

	def _keyframe_delete(self, *args, **kwargs):
		self._object.keyframe_delete(*args, **kwargs)

	def _keyframe_insert(self, *args, **kwargs):
		self._object.keyframe_insert(*args, **kwargs)

	@property
	def _all_objects(self):
		"""List of all objects associated with this object."""
		return [self.object]

	@property
	def location(self) -> Vector:
		"""Location of object"""
		return self.obj.location

	@location.setter
	def location(self, value):
		self.set_location(value)

	@property
	def rotation_euler(self) -> Euler:
		"""Rotation in euler XYZ angles"""
		return self.obj.rotation_euler

	@rotation_euler.setter
	def rotation_euler(self, value):
		self.set_rotation_euler(value)


	@property
	def scale(self):
		return self.obj.scale

	@scale.setter
	def scale(self, scale):
		self.set_scale(scale)


	@animatable_property('location')
	def set_location(self, location: types.VectorLikeAlias):
		"""Set location of object.

		:param location: Location vector to set"""
		location = handle_vec(location, 3)

		translation = location - self.location
		with SelectObjects(self._all_objects):
			bpy.ops.transform.translate(value=translation)


	@animatable_property('rotation_euler')
	def set_rotation_euler(self, rotation: types.VectorLikeAlias):
		"""Set euler rotation of object.

		:param rotation: Rotation vector"""

		assert len(rotation) == 3, f"Rotation must be a tuple of length 3, got {len(rotation)}"
		rotation = Euler(rotation, 'XYZ')
		diff = _euler_from(self.rotation_euler, rotation)

		with SelectObjects(self._all_objects):
			for ax, val in zip('XYZ', diff):
				if val != 0:
					bpy.ops.transform.rotate(value=val, orient_axis=ax)

	@animatable_property('scale')
	def set_scale(self, scale: types.VectorLikeOrScalarAlias):
		"""Set scale of object.

		:param scale: Scale to set. Either single value or 3 long vector"""
		if isinstance(scale, (int, float)):
			scale = (scale, scale, scale)

		resize_fac = np.array(scale) / np.array(self.scale)

		with SelectObjects(self._all_objects):
			bpy.ops.transform.resize(value=resize_fac)

	def translate(self, translation):
		"""Translate object"""
		translation = handle_vec(translation, 3)
		self.location = self.location + translation

	def rotate_by(self, rotation):
		"""Add a rotation to the object. Must be in XYZ order, euler angles, radians."""
		rotation = handle_vec(rotation, 3)
		new_rotation = _euler_add(self.rotation_euler, Euler(rotation, 'XYZ'))
		self.rotation_euler = new_rotation

	def scale_by(self, scale):
		"""Scale object"""
		if isinstance(scale, (int, float)):
			scale = (scale, scale, scale)

		scale = handle_vec(scale, 3)
		self.scale *= scale

	@property
	def matrix_world(self):
		"""Return world matrix of object(s)."""
		bpy.context.evaluated_depsgraph_get()  # required to update object matrix
		return self.object.matrix_world

	@property
	def axes(self) -> np.ndarray:
		"""Return 3x3 rotation matrix (normalized) to represent axes"""
		mat = np.array(self.matrix_world)[:3, :3]
		mat = mat / np.linalg.norm(mat, axis=0)
		return mat

	def track_to(self, obj: Union['BsynObject', bpy.types.Object]):
		"""Track to object.

		:param obj: BsynObject or Blender Object to track to
		"""

		if isinstance(obj, BsynObject):
			obj = obj.obj

		constraint = self.object.constraints.new('TRACK_TO')
		constraint.target = obj
		constraint.track_axis = 'TRACK_NEGATIVE_Z'
		constraint.up_axis = 'UP_Y'

	def untrack(self):
		"""Remove track to constraint from object"""
		constraint = self.object.constraints.get('Track To')
		self.object.constraints.remove(constraint)

	def follow_path(self, path: 'Curve', zero: bool = True,
					animate: bool = True, frames: tuple = (0, 250), fracs: tuple = (0, 1)):
		"""Follow path, with optional animation setting.

		:param path: Curve object
		:param zero: If True, set camera location to (0, 0, 0) [aligns camera with path]
		:param animate: If True, animate camera along path
		:param frames: tuple of keyframes to animate at - length N
		:param fracs: tuple of fractions along path to animate at - length N
		"""

		constraint = self.object.constraints.new('FOLLOW_PATH')
		constraint.target = path.path
		constraint.forward_axis = 'TRACK_NEGATIVE_Z'
		constraint.up_axis = 'UP_Y'
		constraint.use_fixed_location = True  # ensures that offset factor is in 0-1 range

		if zero:
			self.location = (0, 0, 0)

		if animate:
			self.animate_path(frames, fracs)

		# if there are any track constraints, place this constraint first
		# so that the object is not rotated by the track constraint
		track_constraint_idx = self.object.constraints.find('Track To')
		if track_constraint_idx > -1:
			self.object.constraints.move(track_constraint_idx, track_constraint_idx + 1)

	def animate_path(self, frames: tuple = (0, 250), fracs: tuple = (0, 1)):
		"""Animate object along path.

		:param frames: tuple of keyframes to animate at - length N
		:param fracs: tuple of fractions along path to animate at - length N
		"""

		assert len(frames) == len(fracs), f"frames and fracs must be same length - got {len(frames)} and {len(fracs)}"

		for frame, frac in zip(frames, fracs):
			self.path_keyframe(frame, frac)

	def path_keyframe(self, frame: int, offset: float):
		"""Set keyframe for camera path offset

		:param frame: Frame number
		:param offset: Offset fraction (0-1)
		"""
		constraint = self.object.constraints.get('Follow Path')
		if constraint is None:
			raise ValueError(f"Object `{self.__class__}` does not have a 'Follow Path' constraint")

		constraint.offset_factor = offset
		constraint.keyframe_insert(data_path='offset_factor', frame=frame)