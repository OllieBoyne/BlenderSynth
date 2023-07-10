import os.path

import bpy
from .utils import GetNewObject, SelectObjects, handle_vec
from .bsyn_object import BsynObject, animatable_property
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

def get_child_meshes(obj):
	"""Given an object, return all meshes that are children of it. Recursively searches children of children.
	Also returns any child objects that aren't meshes"""
	if obj.type == 'MESH':
		return [obj], []
	else:
		meshes, other = [], [obj]
		for child in obj.children:
			child_meshes, child_other = get_child_meshes(child)
			meshes += child_meshes
			other += child_other

		return meshes, other

def bounds_center(mesh):
	"""Get center of bounding box in world space"""
	local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in mesh.bound_box), mathutils.Vector())
	global_bbox_center = mesh.matrix_world @ local_bbox_center
	return np.array(global_bbox_center)

def vertex_center(mesh):
	"""Get center of vertices in world space"""
	verts = np.array([mesh.matrix_world @ v.co for v in mesh.data.vertices])
	return verts.mean(axis=0)


def _euler_from(a: mathutils.Euler, b: mathutils.Euler):
	"""Get euler rotation from a to b"""
	return (b.to_matrix() @ a.to_matrix().inverted()).to_euler()

def _euler_add(a: mathutils.Euler, b: mathutils.Euler):
	"""Compute euler rotation of a, followed by b"""
	return (a.to_matrix() @ b.to_matrix()).to_euler()


class Mesh(BsynObject):
	"""A mesh object. Can be a single mesh, or a hierarchy of meshes."""
	primitive_list = list(_primitives.keys())
	"""List of available primitives"""

	def __init__(self, obj, material=None, scene=None, class_id=None):
		"""
		:param obj: Receives either a single mesh, or an empty with children empty & meshes
		:param material:
		:param scene:

		If obj contains multiple meshes, they will all be assigned the same material, and must act as a single object
		i.e. they will all be transformed together

		"""

		if scene is None:
			scene = bpy.context.scene

		self.scene = scene
		self._object = obj
		self._meshes, self._other_objects = get_child_meshes(obj)

		# Must have a material, create if not passed
		if material is None:
			material = bpy.data.materials.new(name='Material')
			material.use_nodes = True

			for mesh in self._meshes:
				mesh.data.materials.append(material)

		# INSTANCING - Define InstanceID based on number of meshes in scene
		self._object['instance_id'] = scene.get('NUM_MESHES', 0)
		scene['NUM_MESHES'] = scene.get('NUM_MESHES', 0) + 1  # Increment number of meshes in scene

		# CLASS - Define class based on type of object (e.g. primitive)
		# can be overriden at any point
		self.set_class_id(class_id)

		self.assigned_aovs = []

		# we want to be able to manage scale, rotation and location separately from the children meshes
		self._scale = Vector((1, 1, 1))
		self._rotation_euler = Euler((0, 0, 0))
		self._location = Vector((0, 0, 0))

	def set_class_id(self, class_id):
		assert isinstance(class_id, int), f"Class ID must be an integer, not {type(class_id)}"
		assert class_id >= 0, f"Class ID must be >= 0, not {class_id}"

		self._object['class_id'] = class_id
		self.scene['MAX_CLASSES'] = max(self.scene.get('MAX_CLASSES', 0), class_id)


	@classmethod
	def from_scene(cls, key, class_id=0) -> 'Mesh':
		"""Create object from named object in scene.

		:param key: Name of object in scene
		:param class_id: Class ID to assign to object

		:return: Mesh loaded from scene"""
		obj = bpy.data.objects[key]
		return cls(obj, class_id=class_id)

	@classmethod
	def from_primitive(cls, name='cube', scale=None, location=None, rotation_euler=None, class_id=None, **kwargs) -> 'Mesh':
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
	def from_obj(cls, obj_loc, class_id=None,
				 forward_axis='-Z', up_axis='Y'):
		"""Load object from .obj file.

		Note: we use bpy.ops.wm.obj_import instead of bpy.ops.import_scene.obj because the latter
		causes issues with materials & vertex ordering.
		(Changing vertex ordering makes the use of keypoints difficult.)
		"""
		for axis in (forward_axis, up_axis):
			assert axis in ('X', 'Y', 'Z', '-X', '-Y', '-Z'), f"Axis `{axis}` not valid, must be one of X, Y, Z, -X, -Y, -Z"

		forward_axis = forward_axis.replace('-', 'NEGATIVE_') # e.g. -X -> NEGATIVE_X
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
	def from_glb(cls, glb_loc, class_id=None):
		"""Load object from .glb file"""
		assert os.path.isfile(glb_loc) and glb_loc.endswith(('.glb', '.gtlf')), f"File `{glb_loc}` not a valid .glb file"

		directory, fname = os.path.split(glb_loc)
		importer = GetNewObject(bpy.context.scene)
		with importer:
			bpy.ops.import_scene.gltf(filepath=glb_loc, files=[{"name": fname}])

		if class_id is None:
			class_id = default_ids['loaded_mesh']

		return cls(importer.imported_obj, class_id=class_id)

	@classmethod
	def from_gltf(cls, gltf_loc, class_id=None):
		return cls.from_glb(gltf_loc, class_id=class_id)


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
					raise ValueError(f"Error with setting origin. Expects a list of {len(self._meshes)} 3-long Vector. Received: {origin}")

	def get_all_vertices(self, ref_frame='WORLD'):
		verts = np.array([vert.co[:] + (1,) for mesh in self._meshes for vert in mesh.data.vertices]).T

		if ref_frame == 'LOCAL':
			pass

		elif ref_frame == 'WORLD':
			world_matrix = np.array(self.matrix_world)
			verts = np.dot(world_matrix, verts)

		else:
			raise ValueError(f"Invalid ref_frame: {ref_frame}. Must be one of ['LOCAL', 'WORLD']")

		verts = verts[:3, :] / verts[3, :]  # convert from homogeneous coordinates
		return verts.T


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

	@property
	def matrix_world(self):
		"""Return world matrix of object(s).
		"""
		bpy.context.evaluated_depsgraph_get() # required to update object matrix
		return self._meshes[0].matrix_world

	@property
	def axes(self) -> np.ndarray:
		"""Return 3x3 rotation matrix (normalized) to represent axes"""
		mat = np.array(self.matrix_world)[:3, :3]
		mat = mat / np.linalg.norm(mat, axis=0)
		return mat

	@property
	def location(self):
		return self._location

	@location.setter
	def location(self, location):
		self.set_location(location)


	@property
	def rotation_euler(self):
		return self._rotation_euler

	@rotation_euler.setter
	def rotation_euler(self, rotation):
		self.set_rotation_euler(rotation)

	@property
	def scale(self):
		return self._scale

	@scale.setter
	def scale(self, scale):
		self.set_scale(scale)

	@animatable_property('location')
	def set_location(self, location):
		"""Set location of object"""
		location = handle_vec(location, 3)

		translation = location - self.location
		with SelectObjects(self._meshes + self._other_objects):
			bpy.ops.transform.translate(value=translation)

		self._location = location

	@animatable_property('rotation_euler')
	def set_rotation_euler(self, rotation):
		"""Set euler rotation of object"""
		assert len(rotation) == 3, f"Rotation must be a tuple of length 3, got {len(rotation)}"
		rotation = Euler(rotation, 'XYZ')
		diff = _euler_from(self.rotation_euler, rotation)

		with SelectObjects(self._meshes + self._other_objects):
			for ax, val in zip('XYZ', diff):
				if val != 0:
					bpy.ops.transform.rotate(value=val, orient_axis=ax)

		self._rotation_euler = rotation



	@animatable_property('scale')
	def set_scale(self, scale):
		"""Set scale of object"""
		if isinstance(scale, (int, float)):
			scale = (scale, scale, scale)

		resize_fac = np.array(scale) / np.array(self.scale)

		with SelectObjects(self._meshes + self._other_objects):
			bpy.ops.transform.resize(value=resize_fac)

		self._scale = scale



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
		self.scale = self._scale * scale

	def delete(self, delete_materials:bool=True):
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

	def centroid(self, method:str='median') -> Vector:
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

	def _set_origin_manual(self, origin:Vector, all_meshes=True):
		"""Override to set origin manually. Should only be used by internal functions."""
		if all_meshes:
			for mesh in self._meshes:
				mesh.location = origin
		else:
			self._meshes[0].location = origin

	def origin_to_centroid(self, method:str='bounds'):
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

	def get_keypoints(self, idxs:list=None, position:Union[np.ndarray, List[Vector]] = None) -> List[Vector]:
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