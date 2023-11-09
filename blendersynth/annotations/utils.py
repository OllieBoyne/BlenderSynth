import bpy
from bpy_extras.object_utils import world_to_camera_view
import mathutils
import numpy as np


def project_point_to_image(
    P: mathutils.Vector,
    scene: bpy.types.Scene,
    camera: bpy.types.Camera,
    invert_y: bool = True,
):
    """Return 2D (x, y) image coordinates of a 3D point P.

    :param P: 3D point
    :param scene: Blender scene
    :param camera: Camera to project through
    :param invert_y: if True, y is measured from the top of the image, otherwise from the bottom (Blender measures from bottom)
    """

    ndc_x, ndc_y, ndc_depth = world_to_camera_view(
        scene, camera, P
    )  # normalized device coords
    imgx = scene.render.resolution_x * ndc_x

    if invert_y:
        imgy = scene.render.resolution_y * (1 - ndc_y)  # ndc_y measured from bottom
    else:
        imgy = scene.render.resolution_y * ndc_y

    return imgx, imgy


def project_points(
    points: np.ndarray,
    scene: bpy.types.Scene,
    camera: bpy.types.Camera,
    invert_y: bool = True,
):
    """Project points to image plane.

    :param points: Nx3 matrix of points
    :param scene: Blender scene
    :param camera: Camera to project through
    :param invert_y: if True, y is measured from the top of the image, otherwise from the bottom

    :return: Nx2 matrix of 2D image coordinates"""
    coords_2d = []
    for p in points:
        p_vec = mathutils.Vector(*(p,))
        coords_2d.append(
            project_point_to_image(p_vec, scene, camera, invert_y=invert_y)
        )

    return np.array(coords_2d)
