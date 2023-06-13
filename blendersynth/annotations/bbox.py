import bpy
from .utils import project_points
import mathutils
import numpy as np
from ..blender.mesh import Mesh

BBOX_FMTS = ['x1y1x2y2', 'xywh']

def bounding_box(object: Mesh, camera: bpy.types.Camera = None,
				 scene:bpy.types.Scene=None,
				 return_fmt='x1y1x2y2', normalized=False, invert_y=True):
	"""Get the bounding box of an object in camera space.
	Achieve this by projecting all vertices of the object to the image plane,
	and taking the min/max of the resulting coordinates.

	:param object: Mesh
	:param camera: bpy.types.Camera (if None, use bpy.context.scene.camera)
	:param scene: bpy.types.Scene (if None, use bpy.context.scene)
	:param return_fmt: str, one of ['x1y1x2y2', 'xywh']
	:param normalized: bool, if True, return normalized coordinates (0-1) instead of pixel coordinates
	:param invert_y: bool, if True, y is measured from the top of the image, otherwise from the bottom (Blender measures from bottom)
	"""

	if camera is None:
		camera = bpy.context.scene.camera

	if scene is None:
		scene = bpy.context.scene

	verts = object.get_all_vertices('WORLD')
	coords_2d = project_points(verts, scene, camera, invert_y=invert_y)

	if normalized:
		coords_2d[:, 0] /= scene.render.resolution_x
		coords_2d[:, 1] /= scene.render.resolution_y

	xmin, ymin = coords_2d.min(axis=0)
	xmax, ymax = coords_2d.max(axis=0)


	if return_fmt == 'x1y1x2y2':
		return xmin, ymin, xmax, ymax

	elif return_fmt == 'xywh':
		return xmin, ymin, xmax - xmin, ymax - ymin

	else:
		raise ValueError(f'Invalid return_fmt: {return_fmt}. Must be one of {BBOX_FMTS}')