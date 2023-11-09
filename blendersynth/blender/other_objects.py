from .bsyn_object import BsynObject
import bpy
from ..utils import types
from .utils import GetNewObject


class Empty(BsynObject):
    def __init__(self, obj: bpy.types.Object = None, name=None, **kwargs):
        if obj is None:
            obj = self._create_empty_in_blender(**kwargs)
        self._object = obj

        if name is not None:
            obj.name = name

    @classmethod
    def create(
        cls,
        location: types.VectorLike = None,
        rotation: types.VectorLike = None,
        scale: types.VectorLike = None,
        radius: float = 1.0,
        name=None,
        **kwargs
    ):
        """Create and return a new Empty instance."""
        obj = cls._create_empty_in_blender(location, rotation, scale, radius, **kwargs)
        return cls(obj, name=name)

    @staticmethod
    def _create_empty_in_blender(
        location: types.VectorLike = None,
        rotation: types.VectorLike = None,
        scale: types.VectorLike = None,
        radius: float = 1.0,
        **kwargs
    ) -> bpy.types.Object:
        """Private method to create and return a new Empty object in Blender."""

        importer = GetNewObject(bpy.context.scene)
        kwargs = {
            **kwargs,
            **{
                k: v
                for k, v in zip(
                    ["location", "rotation", "scale", "radius"],
                    [location, rotation, scale, radius],
                )
            },
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        with importer:
            bpy.ops.object.empty_add(**kwargs)

        return importer.imported_obj
