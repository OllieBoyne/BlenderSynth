import bpy
from .bsyn_object import BsynObject

prims = {
    "circle": bpy.ops.curve.primitive_bezier_circle_add,
    "bezier": bpy.ops.curve.primitive_bezier_curve_add,
    "path": bpy.ops.curve.primitive_nurbs_path_add,
}


class Curve(BsynObject):
    """Blender path object"""

    def __init__(
        self, path_type="circle", scale=1, location=(0, 0, 0), rotation=(0, 0, 0)
    ):
        """Create a new path:

        :param path_type: Type of path to create. One of 'circle', 'bezier', 'path' (straight line)
        """

        self.path = None
        self._create_path(path_type)
        self._object = self.path

        self.scale = scale
        self.location = location
        self.rotation = rotation

    def _create_path(self, path_type):
        prims[path_type]()
        self.path = bpy.context.object
