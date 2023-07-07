import bpy
import numpy as np
import mathutils
from typing import Union


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


def handle_vec(vec: Union[tuple, list, np.ndarray], expected_length: int = 3) -> mathutils.Vector:
	"""Check `vec` is expected_length. Convert from tuple or ndarray to mathutils.Vector.

	:param vec: Vector to check
	:param expected_length: Expected length of vector
	"""

	if isinstance(vec, (tuple, list)):
		vec = mathutils.Vector(vec)
	elif isinstance(vec, np.ndarray):
		vec = mathutils.Vector(vec.tolist())
	assert len(vec) == expected_length, "Vector must be length {}".format(expected_length)
	return vec
