import copy

import bpy
from .utils import GetNewObject
from copy import deepcopy

LIGHT_TYPES = ['POINT', 'SUN', 'SPOT', 'AREA']


class Light:
	"""Light object, for managing lights in the scene"""
	light_types = LIGHT_TYPES
	"""List of available light types"""

	def __init__(self, light):
		self.obj = light
		self.__dict__ = copy.deepcopy(light.__dict__)  # copy over attributes from light

	@classmethod
	def from_scene(cls, key):
		"""Create object from scene key

		:param key: Key of object in scene
		:return: :class:`~blendersynth.blender.light.Light` object
		"""
		obj = bpy.data.objects[key]
		return cls(obj)

	@classmethod
	def create(cls, light_type='POINT', name='Light', intensity=1.0, color=(1.0, 1.0, 1.0), location=(0, 0, 0)):
		"""Create a new light object

		:param light_type: Type of light to create (see :attr:`~blendersynth.blender.light.Light.light_types`)
		:param name: Name of light
		:param intensity: Intensity of light
		:param color: Color of light
		:param location: Location of light

		:return: :class:`~blendersynth.blender.light.Light` object

		"""
		assert light_type in LIGHT_TYPES, f"Light type `{light_type}` not found. Options are: {LIGHT_TYPES}"

		light_data = bpy.data.lights.new(name=name, type=light_type)
		light_data.energy = intensity
		light_data.color = color

		light = bpy.data.objects.new(name=name, object_data=light_data)
		light.location = location
		bpy.context.collection.objects.link(light)

		return light

	@property
	def rotation_euler(self):
		"""Rotation of light in euler XYZ angles"""
		return self.obj.rotation_euler

	@rotation_euler.setter
	def rotation_euler(self, value):
		self.obj.rotation_euler = value

	@property
	def location(self):
		"""Location of light"""
		return self.obj.location

	@location.setter
	def location(self, value):
		self.obj.location = value