import bpy
from .utils import project_points
import numpy as np
from .annotation_handler import AnnotationHandler
from ..blender.camera import Camera
from typing import List, Union


def _project_keypoints(
    points3d: np.ndarray, camera: bpy.types.Camera = None, scene: bpy.types.Scene = None
) -> np.ndarray:
    """Project 3D world points to 2D image coordinates.

    Projects using :func:`blendersynth.annotations.utils.project_points`.

    :param points3d: Nx3 array of 3D points
    :param scene: scene to use (if None, `use bpy.context.scene`)
    :param camera: camera to project through (if None, use `bpy.context.scene.camera`)

    :return: Nx2 array of 2D image coordinates
    """

    if scene is None:
        scene = bpy.context.scene

    if camera is None:
        camera = scene.camera

    # project points
    return project_points(points3d, scene, camera)


def project_keypoints(
    points3d: np.ndarray,
    camera: Union[Camera, List[Camera]] = None,
    scene: bpy.types.Scene = None,
) -> AnnotationHandler:
    """Project 3D world points to 2D image coordinates for each camera.

    :param points3d: Nx3 array of 3D points
    :param camera: Either a single :class:`~blendersynth.blender.camera.Camera` object, or a list of them. If None, use bpy.context.scene.camera
    :param scene: bpy.types.Scene (if None, use bpy.context.scene)
    """

    return_dict = {}

    if camera is None:
        camera = bpy.context.scene.camera

    if not isinstance(camera, list):
        camera = [camera]

    for cam in camera:
        return_dict[cam.name] = _project_keypoints(points3d, camera=cam, scene=scene)

    return AnnotationHandler.from_annotations(return_dict, ann_type="keypoints")
