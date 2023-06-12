import bpy
from .utils import project_points
import mathutils
import numpy as np
from ..blender.mesh import Mesh

BBOX_FMTS = ['x1y1x2y2', 'xywh']

def bounding_box(object: Mesh, camera: bpy.types.Camera = None,
				 scene:bpy.types.Scene=None,
				 return_fmt='x1y1x2y2'):
	"""Get the bounding box of an object in camera space.

	:param object: bpy.types.Object
	:param camera: bpy.types.Camera (if None, use bpy.context.scene.camera)
	:param scene: bpy.types.Scene (if None, use bpy.context.scene)
	:param return_fmt: str, one of ['x1y1x2y2', 'xywh']
	"""
	if camera is None:
		camera = bpy.context.scene.camera

	if scene is None:
		scene = bpy.context.scene

	corners = np.stack([object.matrix_world @ mathutils.Vector(corner) for corner in object.bound_box])
	coords_2d = project_points(corners, scene, camera)

	xmin, ymin = coords_2d.min(axis=0)
	xmax, ymax = coords_2d.max(axis=0)

	if return_fmt == 'x1y1x2y2':
		return xmin, ymin, xmax, ymax

	elif return_fmt == 'xywh':
		return xmin, ymin, xmax - xmin, ymax - ymin

	else:
		raise ValueError(f'Invalid return_fmt: {return_fmt}. Must be one of {BBOX_FMTS}')
