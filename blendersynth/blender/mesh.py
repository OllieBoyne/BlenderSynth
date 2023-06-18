import os.path

import bpy
from .utils import GetNewObject, SelectObjects
from .aov import AOV
import numpy as np
import mathutils
from mathutils import Vector, Matrix, Euler

_primitives ={
	"cube": bpy.ops.mesh.primitive_cube_add,
	"sphere": bpy.ops.mesh.primitive_uv_sphere_add,
	"cylinder": bpy.ops.mesh.primitive_cylinder_add,
	"plane": bpy.ops.mesh.primitive_plane_add,
	"cone": bpy.ops.mesh.primitive_cone_add,
	"monkey": bpy.ops.mesh.primitive_monkey_add,
	"torus": bpy.ops.mesh.primitive_torus_add,
}

default_ids = {
	'prim_cube': 0,
	'prim_sphere': 1,
	'prim_cylinder': 2,
	'prim_plane': 3,
	'prim_cone': 4,
	'prim_monkey': 5,
	'prim_torus': 6,
	'loaded_mesh': 7,
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

def set_origin(mesh, vec):
	if mesh.type == 'MESH':
		delta = mesh.location - mathutils.Vector(vec)
		delta_object = mesh.matrix_world.inverted() @ delta
		mesh.data.transform(mathutils.Matrix.Translation(delta_object))  # Move the mesh vertices in the opposite direction
		mesh.location -= delta_object
		bpy.context.view_layer.update()

def handle_vec(vec, expected_length=3):
	"""Check ven is expected_length. Convert from tuple or ndarray to mathutils.Vector """
	if isinstance(vec, (tuple, list)):
		vec = mathutils.Vector(vec)
	elif isinstance(vec, np.ndarray):
		vec = mathutils.Vector(vec.tolist())
	assert len(vec) == expected_length, "Vector must be length {}".format(expected_length)
	return vec

def euler_from(a: mathutils.Euler, b: mathutils.Euler):
	"""Get euler rotation from a to b"""
	return (b.to_matrix() @ a.to_matrix().inverted()).to_euler()

def euler_add(a: mathutils.Euler, b: mathutils.Euler):
	"""Compute euler rotation of a, followed by b"""
	return (a.to_matrix() @ b.to_matrix()).to_euler()


class Mesh:
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
		self.obj = obj
		self._meshes, self._other_objects = get_child_meshes(obj)

		# Must have a material, create if not passed
		if material is None:
			material = bpy.data.materials.new(name='Material')
			material.use_nodes = True

			for mesh in self._meshes:
				mesh.data.materials.append(material)

		# INSTANCING - Define InstanceID based on number of meshes in scene
		self.obj['instance_id'] = scene.get('NUM_MESHES', 0)
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

		self.obj['class_id'] = class_id
		self.scene['MAX_CLASSES'] = max(self.scene.get('MAX_CLASSES', 0), class_id)


	@classmethod
	def from_scene(cls, key, class_id=None):
		"""Create object from scene"""
		obj = bpy.data.objects[key]
		return cls(obj, class_id=class_id)

	@classmethod
	def from_primitive(cls, name='cube', scale=None, class_id=None, **kwargs):
		"""Create object from primitive"""
		assert name in _primitives, f"Primitive `{name}` not found. Options are: {list(_primitives.keys())}"

		importer = GetNewObject(bpy.context.scene)
		with importer:
			prim = _primitives[name](**kwargs)  # Create primitive

		if class_id is None:
			class_id = default_ids[f'prim_{name}']

		obj = cls(importer.imported_obj, class_id=class_id)

		if scale is not None:  # handle scale separately so can be a single value
			obj.scale = scale

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

		forward_axis = axis.replace('-', 'NEGATIVE_') # e.g. -X -> NEGATIVE_X
		up_axis = axis.replace('-', 'NEGATIVE_')

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
	def origin(self):
		"""Get origin as origin of first mesh"""
		return self._meshes[0].location

	@origin.setter
	def origin(self, origin):
		"""Set origin of object"""
		self._meshes[0].location = origin

	def get_all_vertices(self, ref_frame='WORLD'):
		verts = np.array([vert.co[:] + (1,) for vert in self.obj.data.vertices]).T

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
		self.obj.pass_index = index
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
		self.obj.location['XYZ'.index(axis)] += pos - min_pos

	# @property
	# def bound_box(self):
	# 	"""Return bounding box of object(s)"""
	# 	return self.obj.bound_box

	@property
	def matrix_world(self):
		"""Return world matrix of object(s)"""
		bpy.context.evaluated_depsgraph_get() # required to update object matrix

		if len(self._meshes) == 1:
			return self.obj.matrix_world

		else:
			return [m.matrix_world for m in self._meshes]

	@property
	def scale(self):
		"""Return scale of primary mesh."""
		return self._scale

	@scale.setter
	def scale(self, scale):
		"""Set scale of all meshes (scales about origin)"""
		if isinstance(scale, (int, float)):
			scale = (scale, scale, scale)

		resize_fac = np.array(scale) / np.array(self.scale)

		with SelectObjects(self._meshes + self._other_objects):
			bpy.ops.transform.resize(value=resize_fac)

		self._scale = scale

	@property
	def rotation_euler(self):
		"""Return euler rotation of object"""
		return self._rotation_euler

	@rotation_euler.setter
	def rotation_euler(self, rotation):
		"""Set euler rotation of object"""
		assert len(rotation) == 3, f"Rotation must be a tuple of length 3, got {len(rotation)}"
		rotation = Euler(rotation, 'XYZ')
		diff = euler_from(self.rotation_euler, rotation)

		with SelectObjects(self._meshes + self._other_objects):
			for ax, val in zip('XYZ', diff):
				if val != 0:
					bpy.ops.transform.rotate(value=val, orient_axis=ax)

		self._rotation_euler = rotation

	@property
	def location(self):
		"""Return location of object"""
		return self._location

	@location.setter
	def location(self, location):
		"""Set location of object"""
		location = handle_vec(location, 3)

		translation = location - self.location
		with SelectObjects(self._meshes + self._other_objects):
			bpy.ops.transform.translate(value=translation)

		self._location = location

	def translate(self, translation):
		"""Translate object"""
		translation = handle_vec(translation, 3)
		self.location += translation

	def rotate_by(self, rotation):
		"""Add a rotation to the object. Must be in XYZ order, euler angles, radians."""
		rotation = handle_vec(rotation, 3)
		new_rotation = euler_add(self.rotation_euler, Euler(rotation, 'XYZ'))
		self.rotation_euler = new_rotation

	def scale_by(self, scale):
		"""Scale object"""
		if isinstance(scale, (int, float)):
			scale = (scale, scale, scale)

		scale = handle_vec(scale, 3)
		self.scale = self._scale * scale

	def delete(self, delete_materials=True):
		"""Clear mesh from scene & mesh data"""
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

	def centroid(self, method='vertex'):
		"""
		:param method: 'vertex' or 'bounds'
		:return:
		"""
		centroids = []

		for mesh in self._meshes:
			if method == 'vertex':
				centroids.append(vertex_center(mesh))

			elif method == 'bounds':
				centroids.append(bounds_center(mesh))

			else:
				raise ValueError(f"Invalid method: {method}. Must be one of ['vertex', 'bounds']")

		return np.mean(centroids, axis=0)

	def origin_to_centroid(self, method='bounds'):
		"""Move object origin to centroid"""
		centroid = self.centroid(method=method)
		for mesh in self._meshes:
			set_origin(mesh, centroid)