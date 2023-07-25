"""Context managers and operations for handling Blender"""
import inspect

import bpy
import numpy as np
import mathutils
from typing import Union, List, Tuple

# define Blender Array type
blender_array_type = Union[List[float], mathutils.Vector, np.ndarray, Tuple[float, ...], Tuple[int, ...]]
blender_array_or_scalar = Union[blender_array_type, int, float]

def _euler_from(a: mathutils.Euler, b: mathutils.Euler):
	"""Get euler rotation from a to b"""
	return (b.to_matrix() @ a.to_matrix().inverted()).to_euler()


def _euler_add(a: mathutils.Euler, b: mathutils.Euler):
	"""Compute euler rotation of a, followed by b"""
	return (a.to_matrix() @ b.to_matrix()).to_euler()


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


def animatable_property(data_path: str, use_data_object: bool = False) -> callable:
	"""Decorator that wraps around a function to take a frame number and value, and set the property at that frame.

	example usage::

		@animatable('location')
		def set_location(self, value):
			self._location = value

	If you want to set the property at the current frame, use the setter as normal:

	``obj.set_location((1, 2, 3))``

	To set the property at a specific frame, use the decorator:

	``obj.set_location((1, 2, 3), frame=10)``

	Which will call the set_location function, followed by

	``self.object.keyframe_insert(data_path='location', frame=10)``

	:param data_path: the data path of the property to set
	:param use_data_object: whether to use the data object or the object itself
	"""

	def wrapper(func):

		original_sig = inspect.signature(func)
		original_params = list(original_sig.parameters.values())

		def subwrapper(self: 'BsynObject', value, *args, frame=None, **kwargs):
			frame = args[0] if len(args) > 0 else frame
			func(self, value, **kwargs)
			if frame is not None:
				object = self.object if not use_data_object else self.object.data
				object.keyframe_insert(data_path=data_path, frame=frame)


		# store original parameters here - we need them for type hinting
		param_types = {param.name: param.annotation for param in original_params}

		# remove type hints from signature as they will be added to the docstring. Add frame = None
		new_params = \
			[inspect.Parameter(param.name, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=param.default) for param in original_params] + \
			[inspect.Parameter("frame", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None)]

		subwrapper.__signature__ = original_sig.replace(parameters=new_params)

		# We need to make the following updates to the docstring:
		# Add parameter 'frame' (matching indent)
		# Copy type hints from signature (to overcome the lack of sphinx autodoc for runtime docstrings)
		doc_lines = []
		line_gen = (line for line in (func.__doc__ or '').split("\n")) # generator of all lines
		indentation = ''
		started_params = False
		for line in line_gen:
			line_starts_with_params = line.lstrip().startswith(":param")
			doc_lines.append(line)
			if not line_starts_with_params and started_params: # end of param block
				break

			if line_starts_with_params:
				indentation = line[:line.index(":param")]
				name = line.split(':')[1].strip().removeprefix('param ')
				param_type = param_types.get(name, inspect._empty)
				if param_type is not inspect._empty:  # If the parameter has a type hint
					if hasattr(param_type, '__name__'):
						class_name = param_type.__name__

					else: # get class name e.g. blendersynth.utils.Object
						class_name = str(param_type)

					doc_lines.append(f'{indentation}:type {name}: :class:`~{class_name}`')

		# add frame param
		doc_lines.append(f"\n{indentation}:param frame: Optional frame for animating \n{indentation}:type frame: :class:`~int`")

		# add rest of lines
		for line in line_gen:
			doc_lines.append(line)

		subwrapper.__doc__ = "\n".join(doc_lines)

		return subwrapper

	return wrapper
