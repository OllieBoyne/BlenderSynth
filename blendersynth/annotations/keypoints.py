import bpy
from .utils import project_points
import numpy as np

def project_keypoints(points3d: np.ndarray, scene:bpy.types.Scene=None, camera:bpy.types.Camera=None):
	"""Project 3D world points to 2D image coordinates.

	Projects using :func:`blendersynth.annotations.utils.project_points`.

	:param points3d: Nx3 array of 3D points
	:param scene: scene to use (if None, `use bpy.context.scene`)
	:param camera: camera to project through (if None, use `bpy.context.scene.camera`)
	"""

	if scene is None:
		scene = bpy.context.scene

	if camera is None:
		camera = scene.camera

	# project points
	return project_points(points3d, scene, camera).tolist()
