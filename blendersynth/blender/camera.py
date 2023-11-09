import bpy
import numpy as np
import mathutils
from .utils import handle_vec, SelectObjects, animatable_property
from .bsyn_object import BsynObject
from typing import Union
from .mesh import Mesh
from .curve import Curve
from ..utils import types


def _look_at_rotation(
    obj_camera: bpy.types.Object,
    at: mathutils.Vector = mathutils.Vector((0, 0, 0)),
    up: mathutils.Vector = mathutils.Vector((0, 0, 1)),
) -> mathutils.Euler:
    """Rotate camera to look at 'at', with 'up' maintained.

    :param obj_camera: Camera object
    :param at: Point to look at
    :param up: Up vector"""

    camera_position = obj_camera.location

    z_axis = -(
        at - camera_position
    ).normalized()  # Blender forwards is '-z', so use -ve here
    x_axis = up.cross(z_axis)
    y_axis = z_axis.cross(x_axis).normalized()
    is_close = all(abs(i) < 5e-3 for i in x_axis)

    if is_close:
        replacement = y_axis.cross(z_axis).normalized()
        x_axis = replacement

    R = mathutils.Matrix([x_axis, y_axis, z_axis]).transposed()
    euler = R.to_euler()
    return euler


class Camera(BsynObject):
    """Camera object, to handle movement, tracking, etc."""

    def __init__(self, camera: bpy.types.Object = None):
        if camera is None:
            camera = bpy.context.scene.camera

        self.camera = camera
        self._object = camera

    @classmethod
    def create(
        cls,
        name: str = "Camera",
        location: Union[list, tuple, np.ndarray] = None,
        rotation: Union[list, tuple, np.ndarray] = None,
    ) -> "Camera":
        """Create a new camera object.

        :param name: Name of camera
        :param location: Location of camera
        :param rotation_euler: Rotation of camera in euler angles"""

        with SelectObjects():  # revert selection after creating camera
            bpy.ops.object.camera_add(enter_editmode=False, align="VIEW")
            camera = bpy.context.object
            camera.name = name

        cam = cls(camera)

        if location is not None:
            cam.set_location(location)

        if rotation is not None:
            cam.set_rotation_euler(rotation)

        return cam

    @classmethod
    def from_scene(cls, name: str = "Camera") -> "Camera":
        """Create from a named camera in scene

        :param name: Name of camera"""
        assert name in bpy.data.objects, f"Camera {name} does not exist"
        return cls(bpy.data.objects[name])

    def update(self):
        """Update view layer and depsgraph"""
        bpy.context.view_layer.update()
        bpy.context.evaluated_depsgraph_get()

    @property
    def fov(self):
        """Field of view in degrees"""
        return self.camera.data.angle * 180 / np.pi

    @fov.setter
    def fov(self, fov):
        self.set_fov(fov)

    @animatable_property(
        "lens", "data"
    )  # FOV is not animatable, so keyframe focal length instead
    def set_fov(self, fov):
        self.camera.data.angle = fov * np.pi / 180
        self.update()

    @property
    def clip_start(self):
        return self.camera.data.clip_start

    @clip_start.setter
    def clip_start(self, clip_start):
        self.set_clip_start(clip_start)

    @animatable_property("clip_start", "data")
    def set_clip_start(self, clip_start):
        self.camera.data.clip_start = clip_start
        self.update()

    @property
    def clip_end(self):
        return self.camera.data.clip_end

    @clip_end.setter
    def clip_end(self, clip_end):
        self.set_clip_end(clip_end)

    @animatable_property("clip_end", "data")
    def set_clip_end(self, clip_end):
        self.camera.data.clip_end = clip_end
        self.update()

    def look_at(
        self,
        at: types.VectorLike = mathutils.Vector((0, 0, 0)),
        up: types.VectorLike = mathutils.Vector((0, 0, 1)),
    ):
        """Look at a point in space, with up vector.

        :param at: Point to look at
        :param up: Up vector"""
        at = handle_vec(at, 3)
        up = handle_vec(up, 3)

        self.rotation_euler = _look_at_rotation(self.camera, at, up)

    def look_at_object(
        self,
        obj: Union[Mesh, bpy.types.Object],
        up: types.VectorLike = mathutils.Vector((0, 0, 1)),
    ):
        """Look at an object, with up vector.

        :param obj: Object to look at
        :param up: Up vector"""

        if isinstance(obj, Mesh):
            obj = obj.obj

        self.look_at(obj.location, up)

    def place_and_rotate(self, pos, euler):
        self.location = pos
        self.euler = euler

    def place_and_look_at(self, pos, at, up=mathutils.Vector((0, 0, 1))):
        pos = handle_vec(pos)
        at = handle_vec(at)
        up = handle_vec(up)

        self.location = pos
        self.look_at(at, up)
