from typing import Union, List, Tuple
from mathutils import Vector
import numpy as np

types_loc = 'blendersynth.utils.types'

VectorLikeAlias = f'{types_loc}.VectorLike'
VectorLike = Union[Vector, np.ndarray, List, Tuple]
"""A type hint that represents vector-like objects. Can be any of:

- :class:`mathutils.Vector`
- :class:`numpy.ndarray`
- :class:`list`
- :class:`tuple`
"""

VectorLikeOrScalarAlias = f'{types_loc}.VectorLikeOrScalar'
VectorLikeOrScalar = Union[VectorLike, int, float]
"""A type hint that represents vector-like objects. Can be any of:

- :class:`~VectorLike`
- :class:`int`
- :class:`float`
"""