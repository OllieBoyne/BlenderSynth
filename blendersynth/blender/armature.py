"""Armature object for managing pose"""

from .bsyn_object import BsynObject, animatable_property
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


class IKConstraint(BsynObject):
	"""A combination of a PoseBone, object, a Constraint object,
	and an Empty which acts as the target for the IK constraint."""

	def __init__(self, pose_bone: PoseBone, constraint: bpy.types.Constraint, empty: bpy.types.Object):
		self.pose_bone = pose_bone
		self.constraint = constraint
		self.empty = empty
		self._object = empty

	@property
	def bone(self):
		return self.pose_bone

	def remove(self):
		"""Remove this constraint."""
		self.bone.constraints.remove(self.constraint)
		bpy.data.objects.remove(self.empty)

	@property
	def armature(self):
		return self.bone.id_data


class Armature(BsynObject):
	"""This class manages armatures - a collection of posable bones."""

	def __init__(self, object: bpy.types.Armature):
		self._object = object
		self.ik_constraints = []  # for IK constraints

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
			return PoseBone(bone)

		if isinstance(bone, str):
			try:
				bone = self.pose.bones[bone]
			except KeyError:
				raise KeyError(f"Bone `{bone}` not found in armature `{self.name}`")
			return PoseBone(bone)

		raise TypeError(f"Expected bone to be PoseBone, str, or PoseBone, got {type(bone)}")

	def pose_bone(self, bone: Union[str, bpy.types.PoseBone], rotation: types.VectorLikeAlias = None,
				  location: types.VectorLikeAlias = None, scale: types.VectorLikeAlias = None,
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

				for constraint in [*self.ik_constraints]:
					if constraint.bone.name == bone.name:
						constraint.remove()
						self.ik_constraints.remove(constraint)

	def add_ik_constraint(self, bone: Union[str, PoseBone], position: types.VectorLikeAlias,
						  chain_count: int = 0) -> IKConstraint:
		"""
		Translates the given pose bone to a specific position using IK.

		:param bone: The pose bone object, or name of bone, to move.
		:param position: Target position to be placed at.
		:param chain_count: Number of bones to affect in the chain. 0 affects all bones in the chain.
		:return: IKConstraint object, which can be used to modify or remove the IK constraint.
		"""

		bone = self.get_bone(bone)

		# Create an empty to serve as the IK target
		bpy.ops.object.empty_add(location=position)
		empty = bpy.context.object
		empty.name = "IK_Target_For_" + bone.name

		# Add IK constraint to the specified bone
		constraint = bone.constraints.new('IK')
		constraint.target = empty
		constraint.chain_count = chain_count

		bpy.context.view_layer.update()

		ik_constraint = IKConstraint(bone, constraint, empty)
		self.ik_constraints.append(ik_constraint)

		return ik_constraint
