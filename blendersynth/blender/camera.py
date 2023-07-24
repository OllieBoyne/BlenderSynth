import bpy
import numpy as np
import mathutils
from .utils import handle_vec, SelectObjects
from .bsyn_object import BsynObject, animatable_property
from typing import Union
from .mesh import Mesh
from .curve import Curve


def _look_at_rotation(obj_camera: bpy.types.Object,
					 at: mathutils.Vector = mathutils.Vector((0, 0, 0)),
					 up: mathutils.Vector = mathutils.Vector((0, 1, 0))) -> mathutils.Euler:
	"""	Rotate camera to look at 'at', with 'up' maintained.

	:param obj_camera: Camera object
	:param at: Point to look at
	:param up: Up vector"""

	camera_position = obj_camera.location

	z_axis = - (at - camera_position).normalized()  # Blender forwards is '-z', so use -ve here
	x_axis = up.cross(z_axis)
	y_axis = z_axis.cross(x_axis).normalized()
	is_close = all(abs(i) < 5e-3 for i in x_axis)

	if is_close:
		replacement = y_axis.cross(z_axis).normalized()
		x_axis = replacement

	R = mathutils.Matrix([x_axis, y_axis, z_axis]).transposed()
	euler = R.to_euler()
	return euler


class Camera(BsynObject):
	"""Camera object, to handle movement, tracking, etc."""

	def __init__(self, camera: bpy.types.Object = None):
		if camera is None:
			camera = bpy.context.scene.camera

		self.camera = camera
		self._object = camera

	@classmethod
	def create(cls, name: str = 'Camera',
			   location: Union[list, tuple, np.ndarray] = None,
			   rotation: Union[list, tuple, np.ndarray] = None) -> 'Camera':
		"""Create a new camera object.

		:param name: Name of camera
		:param location: Location of camera
		:param rotation_euler: Rotation of camera in euler angles"""

		with SelectObjects():  # revert selection after creating camera
			bpy.ops.object.camera_add(enter_editmode=False, align='VIEW')
			camera = bpy.context.object
			camera.name = name

		cam = cls(camera)

		if location is not None:
			cam.set_location(location)

		if rotation is not None:
			cam.set_rotation_euler(rotation)

		return cam

	@classmethod
	def from_scene(cls, name: str = 'Camera') -> 'Camera':
		"""Create from a named camera in scene

		:param name: Name of camera"""
		assert name in bpy.data.objects, f'Camera {name} does not exist'
		return cls(bpy.data.objects[name])

	def update(self):
		"""Update view layer and depsgraph"""
		bpy.context.view_layer.update()
		bpy.context.evaluated_depsgraph_get()

	@property
	def fov(self):
		"""Field of view in degrees"""
		return self.camera.data.angle * 180 / np.pi

	@fov.setter
	def fov(self, fov):
		self.set_fov(fov)

	@animatable_property('lens', use_data_object=True)  # FOV is not animatable, so keyframe focal length instead
	def set_fov(self, fov):
		self.camera.data.angle = fov * np.pi / 180
		self.update()

	@property
	def location(self):
		return self.camera.location

	@location.setter
	def location(self, pos):
		self.set_location(pos)

	@property
	def rotation_euler(self):
		return self.camera.rotation_euler

	@rotation_euler.setter
	def rotation_euler(self, euler):
		self.set_rotation_euler(euler)

	@animatable_property('location')
	def set_location(self, pos):
		self.camera.location = mathutils.Vector(pos)
		self.update()

	@animatable_property('rotation_euler')
	def set_rotation_euler(self, euler):
		self.camera.rotation_euler = euler
		self.update()

	@property
	def matrix_world(self):
		return self.camera.matrix_world

	@property
	def data(self):
		return self.camera.data

	def look_at(self, at:mathutils.Vector=mathutils.Vector((0, 0, 0)), up:mathutils.Vector=mathutils.Vector((0, 0, 1))):
		"""Look at a point in space, with up vector.

		:param at: Point to look at
		:param up: Up vector"""
		at = handle_vec(at, 3)
		up = handle_vec(up, 3)

		self.rotation_euler = _look_at_rotation(self.camera, at, up)

	def look_at_object(self, obj: Union[Mesh, bpy.types.Object], up:mathutils.Vector=mathutils.Vector((0, 1, 0))):
		"""Look at an object, with up vector.

		:param obj: Object to look at
		:param up: Up vector"""

		if isinstance(obj, Mesh):
			obj = obj.obj

		self.look_at(obj.location, up)

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

	def follow_path(self, path: Curve, zero: bool = True,
					animate: bool = True, frames: tuple = (0, 250), fracs: tuple = (0, 1)):
		"""Follow path, with optional animation setting.

		:param path: Curve object
		:param zero: If True, set camera location to (0, 0, 0) [aligns camera with path]
		:param animate: If True, animate camera along path
		:param frames: tuple of keyframes to animate at - length N
		:param fracs: tuple of fractions along path to animate at - length N
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
			self.camera.constraints.move(track_constraint_idx, track_constraint_idx + 1)

		self.update()

	def animate_path(self, frames: tuple = (0, 250), fracs: tuple = (0, 1)):
		"""Animate camera along path.

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
		constraint = self.camera.constraints.get('Follow Path')
		if constraint is None:
			raise ValueError("Camera does not have a 'Follow Path' constraint")

		constraint.offset_factor = offset
		constraint.keyframe_insert(data_path='offset_factor', frame=frame)

		self.update()
