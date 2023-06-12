import copy

import bpy
from .utils import GetNewObject
from copy import deepcopy

LIGHT_TYPES = ['POINT', 'SUN', 'SPOT', 'AREA']

class Light:
	def __init__(self, light):
		self.__dict__ = copy.deepcopy(light.__dict__)  # copy over attributes from light

	@classmethod
	def from_scene(cls, key):
		"""Create object from scene"""
		obj = bpy.data.objects[key]
		return cls(obj)

	@classmethod
	def create(cls, light_type='POINT', name='Light', intensity=1.0, color=(1.0, 1.0, 1.0), location=(0, 0, 0)):
		"""Create light from primitive"""
		assert light_type in LIGHT_TYPES, f"Light type `{light_type}` not found. Options are: {LIGHT_TYPES}"

		light_data = bpy.data.lights.new(name=name, type=light_type)
		light_data.energy = intensity
		light_data.color = color

		light = bpy.data.objects.new(name=name, object_data=light_data)
		light.location = location
		bpy.context.collection.objects.link(light)

		return light  # Return object