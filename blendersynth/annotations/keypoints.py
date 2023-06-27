import bpy
from .utils import project_points

def project_keypoints(points3d, scene=None, camera=None):
	if scene is None:
		scene = bpy.context.scene

	if camera is None:
		camera = scene.camera

	# project points
	return project_points(points3d, scene, camera).tolist()
