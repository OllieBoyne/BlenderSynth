"""Armature object for managing pose"""

from .bsyn_object import BsynObject, animatable_property
from .other_objects import Empty
from .utils import SelectObjects, SetMode
from typing import Union
from ..utils import types
import bpy
import mathutils



class PoseBone(BsynObject):
	def __init__(self, object: bpy.types.PoseBone):
		self._object = object

	@property
	def name(self) -> str:
		return self.obj.name

	@property
	def constraints(self):
		return self.obj.constraints

	@property
	def armature(self):
		return self.obj.id_data

	@property
	def matrix_world(self):
		return self.armature.matrix_world @ self.obj.matrix

	@property
	def location(self) -> mathutils.Vector:
		"""
		Gets the world location of the head (start) of the bone.
		"""
		return self.obj.head

	@property
	def head_location(self) -> mathutils.Vector:
		"""
		Gets the world location of the head (start) of the bone.
		"""
		return self.armature.matrix_world @ self.obj.head

	@property
	def tail_location(self) -> mathutils.Vector:
		"""
		Gets the world location of the tail (or end) of the bone.
		"""
		return self.armature.matrix_world @ self.obj.tail

	@property
	def rotation_euler(self) -> mathutils.Euler:
		return self.matrix_world.to_euler()

	@animatable_property('scale')
	def set_scale(self, scale: types.VectorLikeOrScalarAlias):
		"""Set scale of pose bone.

		:param scale: Scale to set. Either single value or 3 long vector"""
		if isinstance(scale, (int, float)):
			scale = (scale, scale, scale)

		self.obj.scale = scale

class BoneConstraint(BsynObject):
	"""Generic pose bone constraint object"""
	def __init__(self, pose_bone: PoseBone, constraint: bpy.types.Constraint, empty: Empty):
		self.pose_bone = pose_bone
		self.constraint = constraint
		self.empty = empty
		self._object = empty.obj


	@property
	def name(self):
		return f"{self.constraint.name}: {self.pose_bone.name} -> {self.empty.name}"

	@property
	def bone(self):
		return self.pose_bone

	def remove(self):
		"""Remove this constraint."""
		self.bone.constraints.remove(self.constraint)
		if self.empty is not None:
			self.empty.remove()

	@property
	def armature(self):
		return self.bone.id_data

class Armature(BsynObject):
	"""This class manages armatures - a collection of posable bones."""

	def __init__(self, object: bpy.types.Armature):
		self._object = object
		self.ik_constraints = {}  # for IK constraints
		self.constraints = {} # for generic constraints
		self.pose_bones = {n: PoseBone(b) for n, b in object.pose.bones.items()}

	@property
	def name(self) -> str:
		return self.obj.name

	@property
	def pose(self) -> bpy.types.Pose:
		return self.obj.pose

	def get_bone(self, bone: Union[str, PoseBone, bpy.types.PoseBone]) -> PoseBone:
		"""
		Get bone from armature.

		:param bone_name: Name of bone to get (or PoseBone object)
		:return: PoseBone object
		"""

		if isinstance(bone, PoseBone):
			return bone

		if isinstance(bone, bpy.types.PoseBone):
			return self.pose_bones[bone.name]

		if isinstance(bone, str):
			return self.pose_bones[bone]

		raise TypeError(f"Expected bone to be PoseBone, str, or PoseBone, got {type(bone)}")

	def pose_bone(self, bone: Union[str, bpy.types.PoseBone], rotation: types.VectorLike = None,
				  location: types.VectorLike = None, scale: types.VectorLike = None,
				  frame: int = None):

		"""Set the pose of a bone by giving a Euler XYZ rotation and/or location.

		:param bone: Name of bone to pose, or PoseBone object
		:param rotation: Euler XYZ rotation in radians
		:param location: Location of bone
		:param scale: Scale of bone
		:param frame: Frame to set pose on. If given, will insert keyframe here.
		"""

		with SetMode('POSE', object=self.obj):
			if isinstance(bone, str):
				bone = self.get_bone(bone)

			bone.rotation_mode = 'XYZ'
			if rotation is not None:
				bone.set_rotation_euler(rotation, frame=frame)

			if location is not None:
				bone.set_location(location, frame=frame)

			if scale is not None:
				bone.set_scale(scale, frame=frame)

	def clear_pose(self, rot=True, location=True, scale=True, bones=None):
		"""Clear the pose of the armature.
		For the target bones, sets poses to zero, and removes any IK constraints.

		:param rot: Clear rotation
		:param location: Clear location
		:param scale: Clear scale
		:param bones: List of bones to clear. If not given, will clear all bones.
		"""

		with SetMode('POSE', object=self.obj):
			for bone in self.pose.bones:
				if bones is None or bone.name in bones:
					if rot:
						bone.rotation_euler = (0, 0, 0)
					if location:
						bone.location = (0, 0, 0)
					if scale:
						bone.scale = (1, 1, 1)

				for bone_name in self.ik_constraints.keys():
					if bone_name == bone.name:
						self.ik_constraints[bone_name].remove()  # remove the constraint
						self.ik_constraints.pop(bone_name)  # remove reference to it

				for cname in [*self.constraints.keys()]:
					constraint = self.constraints[cname]
					if constraint.pose_bone.name == bone.name:
						self.constraints[cname].remove()
						self.constraints.pop(cname)


	def add_constraint(self, bone: Union[str, PoseBone], constraint_name: str, target:Empty=None, **kwargs) -> BoneConstraint:
		"""
		Applies a generic bone constraint. Returns BoneConstraint object

		:param bone: Bone to apply constraint to
		:param constraint_name:
		:param target: Empty target. If none given, will create one.

		Any other constraint specific keyword arguments given as well will be fed into the new constraint
		"""

		bone = self.get_bone(bone)

		# Add IK constraint to the specified bone
		constraint = bone.constraints.new(constraint_name)
		for k, v in kwargs.items():
			setattr(constraint, k, v)

		# Create an empty to serve as the IK target
		if target is None:
			target = Empty(name="Target_For_" + bone.name)

		constraint.target = target.object

		bpy.context.view_layer.update()

		constraint = BoneConstraint(bone, constraint, target)
		self.constraints[constraint.name] = constraint

		return constraint
