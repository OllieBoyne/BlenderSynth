"""Context managers and operations for handling Blender"""

import bpy
import numpy as np
import mathutils


class GetNewObject():
	"""Context manager for getting the newly imported object(s) to the scene.

	On exit, will return the newly imported object(s).

	Assumes that either (1) only one object is imported, or (2) there is a hierarchy to the imported objects, and the top level object is the one to return."""

	def __init__(self, scene):
		self.scene = scene
		self.imported_obj = None

	def __enter__(self):
		self.old_objs = set(self.scene.objects)

	def __exit__(self, *args):
		x = set(self.scene.objects) - self.old_objs
		assert len(x) > 0, "No imported objects found..."

		if len(x) == 1:
			self.imported_obj = x.pop()

		else:

			# assume there is a hierarchy to the objects - get the highest
			parent_obj = None
			for obj in x:
				if obj.parent is None:
					parent_obj = obj
					break

			assert parent_obj is not None, "Multiple objects loaded,  but no parent object found..."
			self.imported_obj = parent_obj


class SelectObjects:
	"""Context manager for selecting objects.
	On exit, will reselect the objects that were selected before entering the context."""

	def __init__(self, objects: list = ()):
		"""Initialize with a list of objects to select
		:param objects: list of bpy.types.Object"""
		self.objects = objects

	def __enter__(self):
		self.old_objs = bpy.context.selected_objects
		# deselect all
		bpy.ops.object.select_all(action='DESELECT')

		# select objects
		for obj in self.objects:
			obj.select_set(True)

	def __exit__(self, *args):
		for obj in self.objects:
			obj.select_set(False)

		for obj in self.old_objs:
			obj.select_set(True)


class SetMode:
	"""Context manager for changing the mode of a specific object in Blender (e.g., to 'POSE'),
	returning to the original mode on exit."""

	def __init__(self, target_mode:str, object:bpy.types.Object=None):
		"""Initialize with the target mode and object
		:param target_mode: Mode to set the object to
		:param object: bpy.types.Object to set the mode of"""
		self.target_mode = target_mode.upper()
		self.original_mode = None
		self.obj = object
		self.original_active_object = None

	def __enter__(self):
		self.original_active_object = bpy.context.view_layer.objects.active

		if self.obj:
			bpy.context.view_layer.objects.active = self.obj

		self.original_mode = bpy.context.object.mode
		bpy.ops.object.mode_set(mode=self.target_mode)

	def __exit__(self, type, value, traceback):
		bpy.ops.object.mode_set(mode=self.original_mode)
		bpy.context.view_layer.objects.active = self.original_active_object


def get_node_by_name(node_tree: bpy.types.NodeTree, key: str, raise_error=False) -> bpy.types.Node:
	"""Given a nodetree and a key, return the first node found with label matching key.

	:param node_tree: Node tree to search
	:param key: Key to search for
	:param raise_error: If True, raise KeyError if key not found
	:return: Node with matching label"""
	for node in node_tree.nodes:
		if node.name == key:
			return node

	if raise_error:
		raise KeyError(f"Key {key} not found in node tree!\nLabels are: {[n.name for n in node_tree.nodes]}")


def handle_vec(vec, expected_length: int = 3) -> mathutils.Vector:
	"""Check `vec` is expected_length. Convert from tuple or ndarray to mathutils.Vector.

	:param vec: Vector to check
	:param expected_length: Expected length of vector
	"""

	if isinstance(vec, (tuple, list)):
		vec = mathutils.Vector(vec)
	elif isinstance(vec, np.ndarray):
		vec = mathutils.Vector(vec.tolist())

	if len(vec) != expected_length:
		raise ValueError("Vector must be length {}".format(expected_length))

	return vec
