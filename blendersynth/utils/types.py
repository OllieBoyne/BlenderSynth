from typing import Union, List, Tuple
try:
	from mathutils import Vector
except ImportError:
	Vector = 'mathutils.Vector'

import numpy as np

types_loc = 'blendersynth.utils.types'

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


# convert our type hint to Sphinx so it can be searched for in documentaton
def sphinxify_type_hint(type_hint):

	type_hint_str = str(type_hint)

	# Replace Python types with their Sphinx roles
	type_mapping = {
		'typing.Union': ':py:data:`~typing.Union`\\',
		'Vector': ':py:class:`~mathutils.Vector`',

		# when mathutils.Vector imported as a string, need this line too
		'ForwardRef(\'mathutils.:py:class:`~mathutils.Vector`\')': ':py:class:`~mathutils.Vector`',

		'numpy.ndarray': ':py:class:`~numpy.ndarray`',
		'typing.List': ':py:class:`~typing.List`',
		'typing.Tuple': ':py:data:`~typing.Tuple`',
	}

	# Wrap the type hint in backticks and replace types
	sphinx_type_hint = type_hint_str
	for py_type, sphinx_type in type_mapping.items():
		sphinx_type_hint = sphinx_type_hint.replace(py_type, sphinx_type)

	return sphinx_type_hint


sphinx_mappings = {} # dictionary of Sphinx auto type hint -> Type hint within this file
wrapper_mappings = {} # dictionary of object -> type hint within this file
for k in ['VectorLike', 'VectorLikeOrScalar']:
	obj = globals()[k]
	key = sphinxify_type_hint(obj)
	value = f':class:`{k} <{types_loc}.{k}>`'
	sphinx_mappings[key] = value
	wrapper_mappings[obj] = value

# to avoid circular referencing, we also create some more type hints here (e.g. Mesh)
Mesh = 'blendersynth.blender.mesh.Mesh'

for name in ['Mesh']:
	obj = globals()[name]
	sphinx_mappings[sphinxify_type_hint(obj)] = f':class:`{name} <{obj}>`'