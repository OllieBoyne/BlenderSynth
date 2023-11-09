import bpy
from .utils import project_points
import mathutils
import numpy as np
from ..blender.mesh import Mesh
from typing import List, Union
from .annotation_handler import AnnotationHandler
from ..blender.camera import Camera


def _get_object_axes(
    object: Mesh,
    camera: bpy.types.Camera = None,
    scene: bpy.types.Scene = None,
    normalized=True,
    invert_y=True,
) -> np.ndarray:
    """Get the unit axes of an object in camera space.

    :param object: Mesh
    :param camera: bpy.types.Camera (if None, use bpy.context.scene.camera)
    :param scene: bpy.types.Scene (if None, use bpy.context.scene)
    :param normalized: if True, return normalized coordinates (0-1) instead of pixel coordinates
    :param invert_y: if True, y is measured from the top of the image, otherwise from the bottom (Blender measures from bottom)

    :return: (4 x 2) centroid + 3 pixel positions of ends of unit axes [XYZ] in XY
    """

    if camera is None:
        camera = bpy.context.scene.camera

    if scene is None:
        scene = bpy.context.scene

    if len(object._meshes) > 1:
        raise NotImplementedError("Axes only supported for single meshes")

    centroid = np.array(object.centroid())
    verts = np.concatenate([centroid[None, :], centroid[None, :] + object.axes], axis=0)
    coords_2d = project_points(verts, scene, camera, invert_y=invert_y)

    if normalized:
        coords_2d[:, 0] /= scene.render.resolution_x
        coords_2d[:, 1] /= scene.render.resolution_y

    return coords_2d


def _get_objects_axes(
    objects: List[Mesh],
    camera: bpy.types.Camera = None,
    scene: bpy.types.Scene = None,
    normalized: bool = False,
    invert_y: bool = True,
) -> List[np.ndarray]:
    """Run `get_axes` for multiple objects

    :param objects: List of Mesh objects
    :param camera: bpy.types.Camera (if None, use bpy.context.scene.camera)
    :param scene: bpy.types.Scene (if None, use bpy.context.scene)
    :param normalized: if True, return normalized coordinates (0-1) instead of pixel coordinates
    :param invert_y: if True, y is measured from the top of the image, otherwise from the bottom (Blender measures from bottom)
    """

    return [
        _get_object_axes(
            obj, camera=camera, scene=scene, normalized=normalized, invert_y=invert_y
        )
        for obj in objects
    ]


def get_axes(
    objects: List[Mesh],
    camera: Union[Camera, List[Camera]] = None,
    scene: bpy.types.Scene = None,
    normalized: bool = False,
    invert_y: bool = True,
) -> AnnotationHandler:
    """Project local axes for all objects into all cameras

    :param objects: List of Mesh objects
    :param camera: Either a single :class:`~blendersynth.blender.camera.Camera` object, or a list of them. If None, use bpy.context.scene.camera
    :param scene: bpy.types.Scene (if None, use bpy.context.scene)
    :param normalized: if True, return normalized coordinates (0-1) instead of pixel coordinates
    :param invert_y: if True, y is measured from the top of the image, otherwise from the bottom (Blender measures from bottom)
    """

    return_dict = {}

    if camera is None:
        camera = bpy.context.scene.camera

    if not isinstance(camera, list):
        camera = [camera]

    for cam in camera:
        return_dict[cam.name] = _get_objects_axes(
            objects, camera=cam, scene=scene, normalized=normalized, invert_y=invert_y
        )

    return AnnotationHandler.from_annotations(return_dict, ann_type="axes")
