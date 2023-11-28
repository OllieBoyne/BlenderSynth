from typing import Union, List, Tuple, ForwardRef

try:
    from mathutils import Vector
except ImportError:
    Vector = "mathutils.Vector"

import numpy as np

types_loc = "blendersynth.utils.types"

VectorLike = Union[Vector, np.ndarray, List, Tuple]
"""A type hint that represents vector-like objects. Can be any of:

- :class:`mathutils.Vector`
- :class:`numpy.ndarray`
- :class:`list`
- :class:`tuple`
"""

VectorLikeOrScalar = Union[VectorLike, int, float]
"""A type hint that represents vector-like objects. Can be any of:

- :class:`~VectorLike`
- :class:`int`
- :class:`float`
"""

## Annotations
KeypointOrAxesAnnotation = List[np.ndarray]
"""Keypoint Annotations, an N x 2 ndarray per instance,
or Axes annotation, a 4 x 2 ndarray per instance"""

BboxAnnotation = List[VectorLike]
"""Bbox annotation, a 1D array per instance"""


# convert our type hint to Sphinx so it can be searched for in documentaton
def sphinxify_type_hint(py_type):
    if py_type is List:  # Handle built-in types
        return ":py:class:`typing.List`"
    if py_type is Tuple:
        return ":py:class:`typing.Tuple`"
    if py_type is int:
        return ":py:class:`int`"
    if py_type is float:
        return ":py:class:`float`"

    if isinstance(py_type, ForwardRef):
        return f":py:class:`~{py_type.__forward_arg__}`"

    elif isinstance(py_type, str):
        return f":py:class:`~{py_type}`"

    elif hasattr(py_type, "__origin__") and hasattr(py_type, "__args__"):
        origin = py_type.__origin__
        args = py_type.__args__
        sphinx_args = ", ".join(sphinxify_type_hint(arg) for arg in args)

        if origin is Union:
            origin_name = "Union"
        else:
            origin_name = (
                origin.__name__
                if hasattr(origin, "__name__")
                else str(origin).split(".")[-1]
            )

        return f":py:data:`~typing.{origin_name}`[{sphinx_args}]"

    else:
        return f":py:class:`~{py_type.__module__}.{py_type.__name__}`"


sphinx_mappings = (
    {}
)  # dictionary of Sphinx auto type hint -> Type hint within this file
wrapper_mappings = {}  # dictionary of object -> type hint within this file
for k in [
    "VectorLike",
    "VectorLikeOrScalar",
    "KeypointOrAxesAnnotation",
    "BboxAnnotation",
]:
    obj = globals()[k]
    key = sphinxify_type_hint(obj)
    value = f":class:`{k} <{types_loc}.{k}>`"
    sphinx_mappings[key] = value
    wrapper_mappings[obj] = value

# to avoid circular referencing, we also create some more type hints here (e.g. Mesh)
Mesh = "blendersynth.blender.mesh.Mesh"
Camera = "blendersynth.blender.camera.Camera"

for name in ["Mesh"]:
    obj = globals()[name]
    sphinx_mappings[sphinxify_type_hint(obj)] = f":class:`{name} <{obj}>`"
