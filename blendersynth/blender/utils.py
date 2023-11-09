"""Context managers and operations for handling Blender"""
import inspect

import bpy
import numpy as np
import mathutils
from typing import Union, List, Tuple, TYPE_CHECKING
from ..utils import types
from functools import wraps

# docs-special-members: __init__

if TYPE_CHECKING:
    from .bsyn_object import BsynObject


def _quaternion_equal(a: mathutils.Quaternion, b: mathutils.Quaternion, tol=1e-6):
    """Check if two quaternion rotations are functionally equal"""
    return abs(a.dot(b)) > 1 - tol


def _euler_equal(a: mathutils.Euler, b: mathutils.Euler, tol=1e-6):
    """Check if two euler rotations are equal"""
    return _quaternion_equal(a.to_quaternion(), b.to_quaternion(), tol=tol)


def _euler_from(a: mathutils.Euler, b: mathutils.Euler):
    """Get euler rotation from a to b"""
    return (a.to_quaternion().rotation_difference(b.to_quaternion())).to_euler("XYZ")


def _euler_add(a: mathutils.Euler, b: mathutils.Euler):
    """Compute euler rotation of a, followed by b"""
    return (a.to_quaternion() @ b.to_quaternion()).to_euler("XYZ")


def _euler_invert(a: mathutils.Euler):
    """Invert euler rotation"""
    return a.to_quaternion().inverted().to_euler("XYZ")


def _is_object_valid(obj: bpy.types.Object):
    """Check if object is still available"""
    try:
        x = obj.name
        return True
    except ReferenceError:
        return False


class GetNewObject:
    """Context manager for getting the newly imported object(s) to the scene.

    On exit, will return the newly imported object(s).

    Assumes that either (1) only one object is imported, or (2) there is a hierarchy to the imported objects, and the top level object is the one to return.
    """

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

            assert (
                parent_obj is not None
            ), "Multiple objects loaded,  but no parent object found..."
            self.imported_obj = parent_obj


def _select(obj, state=True):
    """Select/deselect an object"""
    if _is_object_valid(obj):
        if hasattr(obj, "select_set"):  # e.g. Mesh
            obj.select_set(state)
        elif hasattr(obj, "select"):  # e.g. PoseBone
            obj.select = state


class SelectObjects:
    """Context manager for selecting objects.
    On exit, will reselect the objects that were selected before entering the context.
    """

    def __init__(
        self,
        objects: List[bpy.types.Object] = (),
        active_object: bpy.types.Object = None,
    ):
        """Initialize with a list of objects to select

        :param objects: list of bpy.types.Object
        :param active_object: [Optional] The `active object <https://docs.blender.org/manual/en/latest/scene_layout/object/selecting.html#>`_ to set
        """

        self.objects = objects

        if active_object is not None:
            if active_object not in self.objects:
                self.objects.append(active_object)

            bpy.context.view_layer.objects.active = active_object

        self.mode = bpy.context.mode
        assert self.mode in [
            "OBJECT",
            "POSE",
            "EDIT",
        ], "Currently only OBJECT, POSE, EDIT supported for SelectObjects"

        self._ops = None
        if self.mode == "OBJECT":
            self._ops = bpy.ops.object
        elif self.mode == "POSE":
            self._ops = bpy.ops.pose
        elif self.mode == "EDIT":
            self._ops = bpy.ops.edit

    def __enter__(self):
        self.old_objs = bpy.context.selected_objects
        # deselect all
        self._ops.select_all(action="DESELECT")

        # select objects
        for obj in self.objects:
            _select(obj, state=True)

    def __exit__(self, *args):
        for obj in self.objects:
            _select(obj, state=False)

        for obj in self.old_objs:
            _select(obj, state=True)


class SetMode:
    """Context manager for changing the mode of a specific object in Blender (e.g., to `POSE`),
    returning to the original mode on exit."""

    def __init__(self, target_mode: str, object: bpy.types.Object = None):
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

        if _is_object_valid(self.original_active_object):
            bpy.context.view_layer.objects.active = self.original_active_object


class CursorAt:
    """Context manager for moving the cursor to a specific location in space.
    On exit, will return the cursor to its original location."""

    def __init__(self, target: types.VectorLike):
        """Initialize with the target location

        :param target: Location to move the cursor to"""

        self.original_location = None
        self.target = target

    def __enter__(self):
        self.original_location = bpy.context.scene.cursor.location.copy()
        bpy.context.scene.cursor.location = self.target

    def __exit__(self, *args):
        bpy.context.scene.cursor.location = self.original_location


def get_node_by_name(
    node_tree: bpy.types.NodeTree, key: str, raise_error: bool = False
) -> bpy.types.Node:
    """Given a nodetree and a key, return the first node found with label matching key.

    :param node_tree: Node tree to search
    :param key: Key to search for
    :param raise_error: If True, raise KeyError if key not found
    :return: Node with matching label"""
    for node in node_tree.nodes:
        if node.name == key:
            return node

    if raise_error:
        raise KeyError(
            f"Key {key} not found in node tree!\nLabels are: {[n.name for n in node_tree.nodes]}"
        )


def handle_vec(vec: types.VectorLike, expected_length: int = 3) -> mathutils.Vector:
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


def animatable_property(data_path: str, id_path: str = "") -> callable:
    """Decorator that wraps around a function to take a frame number and value, and set the property at that frame.

    Example usage::

            @animatable('location')
            def set_location(self, value):
                    self._location = value

    If you want to set the property at the current frame, use the setter as normal:

    ``obj.set_location((1, 2, 3))``

    To set the property at a specific frame, simply add the frame keyword:

    ``obj.set_location((1, 2, 3), frame=10)``

    Which is functionally equivalent to::

            obj.set_location((1, 2, 3))
            obj.object.keyframe_insert(data_path='location', frame=10)

    :param data_path: the data path of the property to set
    :param id_path: Use for animating ID blocks other than object (e.g. 'data')
    """

    def wrapper(func):
        original_sig = inspect.signature(func)
        original_params = list(original_sig.parameters.values())

        def subwrapper(self: "BsynObject", value, *args, frame=None, **kwargs):
            frame = args[0] if len(args) > 0 else frame
            func(self, value, **kwargs)
            if frame is not None:
                object = self.object if id_path == "" else eval(f"self.{id_path}")
                object.keyframe_insert(data_path=data_path, frame=frame)

        # store original parameters here - we need them for type hinting
        param_types = {param.name: param.annotation for param in original_params}

        # remove type hints from signature as they will be added to the docstring. Add frame = None
        new_params = [
            inspect.Parameter(
                param.name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=param.default,
            )
            for param in original_params
        ] + [
            inspect.Parameter(
                "frame", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None
            )
        ]

        subwrapper.__signature__ = original_sig.replace(parameters=new_params)

        # We need to make the following updates to the docstring:
        # Add parameter 'frame' (matching indent)
        # Copy type hints from signature (to overcome the lack of sphinx autodoc for runtime docstrings)
        doc_lines = []
        line_gen = (
            line for line in (func.__doc__ or "").split("\n")
        )  # generator of all lines
        indentation = ""
        started_params = False
        for line in line_gen:
            line_starts_with_params = line.lstrip().startswith(":param")
            doc_lines.append(line)
            if not line_starts_with_params and started_params:  # end of param block
                break

            if line_starts_with_params:
                indentation = line[: line.index(":param")]
                name = line.split(":")[1].strip().removeprefix("param ")
                param_type = param_types.get(name, inspect._empty)
                if param_type is not inspect._empty:  # If the parameter has a type hint
                    # For custom classes
                    if param_type in types.wrapper_mappings:
                        new_line = f"{indentation}:type {name}: {types.wrapper_mappings[param_type]}"

                    # For built-in classes
                    else:
                        if hasattr(param_type, "__name__"):
                            class_name = param_type.__name__

                        else:  # get class name e.g. blendersynth.utils.Object
                            class_name = str(param_type)

                        new_line = f"{indentation}:type {name}: :class:`~{class_name}`"

                    doc_lines.append(new_line)

        # add frame param
        doc_lines.append(
            f"\n{indentation}:param frame: Optional frame for animating \n{indentation}:type frame: :class:`~int`"
        )

        # add rest of lines
        for line in line_gen:
            doc_lines.append(line)

        subwrapper.__doc__ = "\n".join(doc_lines)

        return subwrapper

    return wrapper
