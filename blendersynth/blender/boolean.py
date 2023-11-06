"""Functions for boolean operations of meshes"""
import bpy
from ..utils import types


def _apply_boolean(
    target: types.Mesh,
    *others: types.Mesh,
    operation: str = "UNION",
    hide_others: bool = True
) -> types.Mesh:
    for other in others:
        target.add_child(other)

        modifier = target.obj.modifiers.new(type="BOOLEAN", name="bool")
        modifier.object = other.obj
        modifier.operation = operation

        bpy.ops.object.modifier_apply(modifier="bool")
        if hide_others:
            other.obj.hide_render = True
            other.obj.hide_set(True)
    return target


def union(target: types.Mesh, *others: types.Mesh, hide_others=True) -> types.Mesh:
    """Apply the union boolean modifier to a collection of meshes.

    :param target: The target Mesh: this is returned by the function
    :param others: Other Meshes to union with `target`
    :param hide_others: If True, hide all Meshes in the `others` list"""
    return _apply_boolean(target, *others, operation="UNION", hide_others=hide_others)


def difference(target: types.Mesh, *others: types.Mesh, hide_others=True) -> types.Mesh:
    """Apply the difference boolean modifier to a collection of meshes.

    :param target: The target Mesh: this is returned by the function
    :param others: Other Meshes to subtract from `target`
    :param hide_others: If True, hide all Meshes in the `others` list"""

    return _apply_boolean(
        target, *others, operation="DIFFERENCE", hide_others=hide_others
    )


def intersect(target: types.Mesh, *others: types.Mesh, hide_others=True) -> types.Mesh:
    """Apply the intersect boolean modifier to a collection of meshes.

    :param target: The target Mesh: this is returned by the function
    :param others: Other Meshes to intersect with `target`
    :param hide_others: If True, hide all Meshes in the `others` list"""
    return _apply_boolean(
        target, *others, operation="INTERSECT", hide_others=hide_others
    )
