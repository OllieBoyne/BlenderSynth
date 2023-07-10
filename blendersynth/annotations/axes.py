import bpy
from .utils import project_points
import mathutils
import numpy as np
from ..blender.mesh import Mesh
from typing import List

def get_axes(object: Mesh, camera: bpy.types.Camera = None,
				 scene:bpy.types.Scene=None,
				 normalized=True,
				 invert_y=True) -> tuple:
	"""Get the unit axes of an object in camera space.

	Return in (4 x 2) centroid + 3 pixel positions of ends of unit axes [XYZ] in XY

	:param object: Mesh
	:param camera: bpy.types.Camera (if None, use bpy.context.scene.camera)
	:param scene: bpy.types.Scene (if None, use bpy.context.scene)
	:param normalized: if True, return normalized coordinates (0-1) instead of pixel coordinates
	:param invert_y: if True, y is measured from the top of the image, otherwise from the bottom (Blender measures from bottom)
	"""

	if camera is None:
		camera = bpy.context.scene.camera

	if scene is None:
		scene = bpy.context.scene

	if len(object._meshes) > 1:
		raise NotImplementedError('Axes only supported for single meshes')

	centroid = np.array(object.centroid())
	verts = np.concatenate([centroid[None, :], centroid[None, :] + object.axes], axis=0)
	coords_2d = project_points(verts, scene, camera, invert_y=invert_y)

	if normalized:
		coords_2d[:, 0] /= scene.render.resolution_x
		coords_2d[:, 1] /= scene.render.resolution_y

	return coords_2d

def get_multiple_axes(objects: List[Mesh], camera: bpy.types.Camera = None,
				 scene:bpy.types.Scene=None,
				 normalized:bool=False, invert_y:bool=True) -> List[tuple]:
	"""Run `get_axes` for multiple objects

	:param objects: List of Mesh objects
	:param camera: bpy.types.Camera (if None, use bpy.context.scene.camera)
	:param scene: bpy.types.Scene (if None, use bpy.context.scene)
	:param normalized: if True, return normalized coordinates (0-1) instead of pixel coordinates
	:param invert_y: if True, y is measured from the top of the image, otherwise from the bottom (Blender measures from bottom)
	"""

	return [get_axes(obj, camera=camera, scene=scene,
						   normalized=normalized, invert_y=invert_y) for obj in objects]