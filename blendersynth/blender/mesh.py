import os.path

import bpy
from .utils import GetNewObject, SelectObjects, handle_vec, SetMode, animatable_property
from .bsyn_object import BsynObject
from .material import Material
from .aov import AOV
import numpy as np
import mathutils
from mathutils import Vector, Euler
from typing import Union, List
from copy import deepcopy

_primitives = {
	"cube": bpy.ops.mesh.primitive_cube_add,
	"sphere": bpy.ops.mesh.primitive_uv_sphere_add,
	"cylinder": bpy.ops.mesh.primitive_cylinder_add,
	"plane": bpy.ops.mesh.primitive_plane_add,
	"cone": bpy.ops.mesh.primitive_cone_add,
	"monkey": bpy.ops.mesh.primitive_monkey_add,
	"torus": bpy.ops.mesh.primitive_torus_add,
}

default_ids = {
	'loaded_mesh': 0,
	'prim_cube': 1,
	'prim_sphere': 2,
	'prim_cylinder': 3,
	'prim_plane': 4,
	'prim_cone': 5,
	'prim_monkey': 6,
	'prim_torus': 7,
}


def _get_child_meshes(obj):
	"""Given an object, return all meshes that are children of it. Recursively searches children of children.
	Also returns any child objects that aren't meshes"""
	if obj.type == 'MESH':
		return [obj], []
	else:
		meshes, other = [], [obj]
		for child in obj.children:
			child_meshes, child_other = _get_child_meshes(child)
			meshes += child_meshes
			other += child_other

		return meshes, other



class Mesh(BsynObject):
	"""A mesh object. Can be a single mesh, or a hierarchy of meshes."""
	primitive_list = list(_primitives.keys())
	"""List of available primitives"""

	def __init__(self, obj, material=None, scene=None, class_id=None):
		"""
		:param obj: Receives either a single mesh, or an empty with children empty & meshes
		:param material: bpy.types.Material to assign to the mesh
		:param scene:

		If obj contains multiple meshes, they will all be assigned the same material, and must act as a single object
		i.e. they will all be transformed together

		"""

		if scene is None:
			scene = bpy.context.scene

		self.scene = scene
		self._object = obj
		self._meshes, self._other_objects = _get_child_meshes(obj)

		# Manage materials here
		if material is not None:
			self._material = Material.from_blender_material(material)
		else:
			self._material = Material('NewMaterial')

		for mesh in self._meshes:
			mesh.data.materials.append(self._material.object)

		# INSTANCING - Define InstanceID based on number of meshes in scene
		self._object['instance_id'] = scene.get('NUM_MESHES', 0)
		scene['NUM_MESHES'] = scene.get('NUM_MESHES', 0) + 1  # Increment number of meshes in scene

		# CLASS - Define class based on type of object (e.g. primitive)
		# can be overriden at any point
		self.set_class_id(class_id)

		self.assigned_aovs = []

	def set_class_id(self, class_id):
		assert isinstance(class_id, int), f"Class ID must be an integer, not {type(class_id)}"
		assert class_id >= 0, f"Class ID must be >= 0, not {class_id}"

		self._object['class_id'] = class_id
		self.scene['MAX_CLASSES'] = max(self.scene.get('MAX_CLASSES', 0), class_id)

	@classmethod
	def from_scene(cls, key:str, class_id:int=0) -> 'Mesh':
		"""Create object from named object in scene.

		:param key: Name of object in scene
		:param class_id: Class ID to assign to object

		:return: Mesh loaded from scene"""
		obj = bpy.data.objects[key]
		return cls(obj, class_id=class_id)

	@classmethod
	def from_primitive(cls, name='cube', scale=None, location=None, rotation_euler=None, class_id=None,
					   **kwargs) -> 'Mesh':
		"""Create Mesh from primitive.
		
		:param name: Name of primitive to create. See :attr:`~blendersynth.blender.Mesh.primitive_list` for options
		:param scale: Scale of object
		:param location: Location of object
		:param rotation_euler: Rotation of object
		:param class_id: Class ID to assign to object
		:param kwargs: Additional arguments to pass to primitive (see `bpy.ops.mesh.primitive_cube_add <https://docs.blender.org/api/current/bpy.ops.mesh.html#bpy.ops.mesh.primitive_cube_add>`_, etc.)

		:return: Mesh object created from primitive
		"""

		assert name in _primitives, f"Primitive `{name}` not found. Options are: {list(_primitives.keys())}"

		importer = GetNewObject(bpy.context.scene)
		with importer:
			prim = _primitives[name](**kwargs)  # Create primitive

		if class_id is None:
			class_id = default_ids[f'prim_{name}']

		obj = cls(importer.imported_obj, class_id=class_id)

		if scale is not None: obj.scale = scale
		if location is not None: obj.location = location
		if rotation_euler is not None: obj.rotation_euler = rotation_euler

		return obj

	@classmethod
	def from_obj(cls, obj_loc:str, class_id:int=None,
				 forward_axis:str='-Z', up_axis:str='Y'):
		"""Load object from .obj file.

		:param obj_loc: Location of .obj file
		:param class_id: Class ID to assign to object
		:param forward_axis: Axis to use as forward axis
		:param up_axis: Axis to use as up axis


		Note: we use bpy.ops.wm.obj_import instead of bpy.ops.import_scene.obj because the latter
		causes issues with materials & vertex ordering.
		(Changing vertex ordering makes the use of keypoints difficult.)
		"""
		for axis in (forward_axis, up_axis):
			assert axis in (
			'X', 'Y', 'Z', '-X', '-Y', '-Z'), f"Axis `{axis}` not valid, must be one of X, Y, Z, -X, -Y, -Z"

		forward_axis = forward_axis.replace('-', 'NEGATIVE_')  # e.g. -X -> NEGATIVE_X
		up_axis = up_axis.replace('-', 'NEGATIVE_')

		assert os.path.isfile(obj_loc) and obj_loc.endswith('.obj'), f"File `{obj_loc}` not a valid .obj file"

		directory, fname = os.path.split(obj_loc)
		directory = os.path.abspath(directory)  # ensure absolute path for clean loading

		importer = GetNewObject(bpy.context.scene)
		with importer:
			bpy.ops.wm.obj_import(filepath=fname, directory=directory, filter_image=False,
								  files=[{"name": fname}], forward_axis=forward_axis, up_axis=up_axis)

		if class_id is None:
			class_id = default_ids['loaded_mesh']

		obj = importer.imported_obj
		return cls(obj, class_id=class_id)

	@classmethod
	def from_glb(cls, glb_loc:str, class_id:int=None):
		"""Load object from .glb file.

		:param glb_loc: Location of .glb file
		:param class_id: Class ID to assign to object
		"""
		assert os.path.isfile(glb_loc) and glb_loc.endswith(
			('.glb', '.gtlf')), f"File `{glb_loc}` not a valid .glb file"

		directory, fname = os.path.split(glb_loc)
		importer = GetNewObject(bpy.context.scene)
		with importer:
			bpy.ops.import_scene.gltf(filepath=glb_loc, files=[{"name": fname}])

		if class_id is None:
			class_id = default_ids['loaded_mesh']

		return cls(importer.imported_obj, class_id=class_id)

	@classmethod
	def from_gltf(cls, gltf_loc:str, class_id:int=None):
		"""Alias for :meth:`~blendersynth.blender.Mesh.from_glb`"""
		return cls.from_glb(gltf_loc, class_id=class_id)

	@classmethod
	def from_fbx(cls, fbx_loc:str, class_id:int=None):
		"""Load object from .fbx file.

		:param fbx_loc: Location of .fbx file
		:param class_id: Class ID to assign to object"""
		assert os.path.isfile(fbx_loc) and fbx_loc.endswith('.fbx'), f"File `{fbx_loc}` not a valid .fbx file"

		directory, fname = os.path.split(fbx_loc)
		importer = GetNewObject(bpy.context.scene)
		with importer:
			bpy.ops.import_scene.fbx(filepath=fbx_loc, files=[{"name": fname}])

		if class_id is None:
			class_id = default_ids['loaded_mesh']

		return cls(importer.imported_obj, class_id=class_id)

	@property
	def origin(self) -> Union[Vector, List[Vector]]:
		"""
		If single mesh, return Vector of origin.
		If multiple meshes, return list of Vectors of centroid of each mesh."""
		if len(self._meshes) == 1:
			return self._meshes[0].location

		else:
			return [m.location for m in self._meshes]

	@origin.setter
	def origin(self, origin):
		"""Set origin of object.
		If single mesh, expects Vector.
		If multiple meshes, expects list of Vectors"""

		if len(self._meshes) == 1:
			try:
				vec = handle_vec(origin)
			except ValueError:
				raise ValueError(f"Error with setting origin. Expects a 3 long Vector. Received: {origin}")

			self._meshes[0].location = vec

		else:
			for i in range(len(self._meshes)):
				try:
					vec = handle_vec(origin[i])
					self._meshes[i].location = vec
				except:
					raise ValueError(
						f"Error with setting origin. Expects a list of {len(self._meshes)} 3-long Vector. Received: {origin}")

	def get_all_vertices(self, ref_frame='WORLD'):
		if ref_frame not in {'LOCAL', 'WORLD'}:
			raise ValueError(f"Invalid ref_frame: {ref_frame}. Must be one of ['LOCAL', 'WORLD']")

		verts = []

		for mesh in self._meshes:
			mesh_verts = np.array([vert.co for vert in mesh.data.vertices])

			if ref_frame == 'WORLD':
				mesh_verts = np.dot(mesh.matrix_world, np.vstack((mesh_verts.T, np.ones(mesh_verts.shape[0]))))

			verts.append(mesh_verts)

		verts = np.concatenate(verts, axis=1)
		verts /= verts[3]  # convert from homogeneous coordinates
		return verts[:3].T

	@property
	def materials(self):
		return {m for mesh in self._meshes for m in mesh.data.materials}

	def assign_pass_index(self, index: int):
		"""Assign pass index to object. This can be used when mask rendering."""
		for mesh in self._meshes:
			mesh.pass_index = index
		return index

	def assign_aov(self, aov: AOV):
		"""Assign AOV to object. Applies to all materials"""
		if aov not in self.assigned_aovs:
			for material in self.materials:
				shader_node_tree = material.node_tree
				assert shader_node_tree is not None, "Material must have a node tree"
				aov.add_to_shader(shader_node_tree)

		self.assigned_aovs.append(aov)

	def set_minimum_to(self, axis='Z', pos=0):
		"""Set minimum of object to a given position"""
		min_pos = self.get_all_vertices('WORLD')[:, 'XYZ'.index(axis)].min()
		trans_vec = np.zeros(3)
		trans_vec['XYZ'.index(axis)] = pos - min_pos
		self.translate(trans_vec)


	def delete(self, delete_materials: bool = True):
		"""Clear mesh from scene & mesh data.

		:param delete_materials: Also delete object materials from scene"""
		mesh_names = [m.name for m in self._meshes]
		for mesh in self._meshes:
			bpy.data.objects.remove(mesh, do_unlink=True)

		# remove any non-mesh objects
		for obj in self._other_objects:
			bpy.data.objects.remove(obj, do_unlink=True)

		# Also remove its mesh data from bpy.data.meshes
		for mname in mesh_names:
			for m in bpy.data.meshes:
				if m.name == mname:
					bpy.data.meshes.remove(m)
					break

		self._meshes = []  # clear mesh list

		if delete_materials:
			for material in self.materials:
				bpy.data.materials.remove(material, do_unlink=True)

	def centroid(self, method: str = 'median') -> Vector:
		"""
		Return the centroid of the mesh(es)

		:param method: See :attr:`~blendersynth.blender.mesh.Mesh.origin_to_centroid` for options.
		:return: Centroid of the mesh(es). If multiple meshes, will average the centroids.
		"""

		original_origins = deepcopy(self.origin)
		self.origin_to_centroid(method=method)
		centroid = deepcopy(self.origin)
		self.origin = original_origins

		if len(self._meshes) > 1:
			return sum(centroid) / len(self._meshes)

		return centroid

	def _set_origin_manual(self, origin: Vector, all_meshes=True):
		"""Override to set origin manually. Should only be used by internal functions."""
		if all_meshes:
			for mesh in self._meshes:
				mesh.location = origin
		else:
			self._meshes[0].location = origin

	def origin_to_centroid(self, method: str = 'bounds'):
		"""Move object origin to centroid.

		Four methods available:

		* 'bounds' - move the origin to the center of the bounds of the mesh
		* 'median' - move the origin to the median point of the mesh
		* 'com_volume' - move to the centre of mass of the volume of the mesh
		* 'com_area' - Move to the centre of mass of the surface of the mesh

		:param method: Selected method to move origin to centroid
		"""

		_valid_methods = ['bounds', 'median', 'com_volume', 'com_area']

		_type_lookup = dict(bounds='ORIGIN_GEOMETRY', median='ORIGIN_GEOMETRY',
							com_volume='ORIGIN_CENTER_OF_VOLUME',
							com_area='ORIGIN_CENTER_OF_MASS')

		center = 'BOUNDS' if method == 'bounds' else 'MEDIAN'

		with SelectObjects(self._meshes + self._other_objects):
			bpy.ops.object.origin_set(type=_type_lookup[method], center=center)

	def get_keypoints(self, idxs: list = None, position: Union[np.ndarray, List[Vector]] = None) -> List[Vector]:
		"""Return 3D keypoint positions in world coordinates, given either:

		:param idxs: list of indices or ndarray of keypoints to project (only valid for single-mesh objects)
		:param position: 3D position of keypoints to project - in LOCAL object coordinates

		:return: N list of Vectors of keypoints in world space, where N is the number of keypoints
		"""

		assert (idxs is not None) ^ (position is not None), "Must provide either idxs or position, but not both."

		if idxs is not None:
			assert len(self._meshes) == 1, "Can only project keypoints by index for single-mesh objects."
			kps3d = [self.matrix_world @ self._meshes[0].data.vertices[i].co for i in idxs]

		elif position is not None:
			kps3d = [self.matrix_world @ p for p in position]

		return kps3d

	@property
	def name(self):
		return self._meshes[0].name

	def get_armature(self, armature_name: str = None) -> bpy.types.Object:
		"""Get armature.
		If no name given, return first armature found.

		:param armature_name: Name of armature to load."""

		armatures = [obj for obj in self._other_objects if obj.type == 'ARMATURE']

		if armature_name:
			for arm in armatures:
				if arm.name == armature_name:
					return arm

			raise KeyError(f"Armature `{armature_name}` not found.")

		else:
			if len(armatures) == 0:
				raise ValueError("No armatures found.")

			return armatures[0]

	def get_bone(self, bone_name: str, armature_name: str = None) -> bpy.types.PoseBone:
		"""
		Get bone from armature.
		:param bone_name:
		:param armature_name: If not given, will load first available armature found
		:return:
		"""

		armature = self.get_armature(armature_name)
		try:
			bone = armature.pose.bones[bone_name]
		except KeyError:
			raise KeyError(f"Bone `{bone_name}` not found in armature `{armature.name}`")
		return bone

	def pose_bone(self, bone: Union[str, bpy.types.PoseBone], rotation: Vector = None, location: Vector = None,
				  armature_name: str = None, frame: int = None):
		"""Set the pose of a bone by giving a Euler XYZ rotation and/or location.

		:param bone: Name of bone to pose, or PoseBone object
		:param rotation: Euler XYZ rotation in radians
		:param location: Location in object space
		:param armature_name: Name of armature to use. If not given, will use first armature found.
		:param frame: Frame to set pose on. If given, will insert keyframe here.
		"""


		with SelectObjects(self._meshes + self._other_objects):
			armature = self.get_armature(armature_name)
			with SetMode('POSE', object = armature):
				if isinstance(bone, str):
					bone = self.get_bone(bone, armature_name)

				bone.rotation_mode = 'XYZ'
				if rotation is not None:
					bone.rotation_euler = rotation
					if frame is not None:
						bone.keyframe_insert(data_path='rotation_euler', frame=frame)

				if location is not None:
					bone.location = location
					if frame is not None:
						bone.keyframe_insert(data_path='location', frame=frame)

	@property
	def material(self):
		return self._material

	@material.setter
	def material(self, material: Material):
		self._material = material
		for mesh in self._meshes:
			mesh.data.materials.clear()
			mesh.data.materials.append(material.object)