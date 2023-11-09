import copy

import bpy
from .utils import GetNewObject, animatable_property
from .bsyn_object import BsynObject
from ..utils import types

LIGHT_TYPES = ["POINT", "SUN", "SPOT", "AREA"]


class Light(BsynObject):
    """Light object, for managing lights in the scene"""

    light_types = LIGHT_TYPES
    """List of available light types"""

    def __init__(self, light):
        self._object = light

    @classmethod
    def from_scene(cls, key):
        """Create object from scene key

        :param key: Key of object in scene
        :return: :class:`~blendersynth.blender.light.Light` object
        """
        obj = bpy.data.objects[key]
        return cls(obj)

    @classmethod
    def create(
        cls,
        light_type: str = "POINT",
        name: str = "Light",
        intensity: float = 1.0,
        color: types.VectorLike = (1.0, 1.0, 1.0),
        location: types.VectorLike = (0, 0, 0),
    ):
        """Create a new Light object

        :param light_type: Type of light to create (see :attr:`~blendersynth.blender.light.Light.light_types`)
        :param name: Name of light
        :param intensity: Intensity of light
        :param color: Color of light
        :param location: Location of light

        :return: :class:`~blendersynth.blender.light.Light` object

        """
        assert (
            light_type in LIGHT_TYPES
        ), f"Light type `{light_type}` not found. Options are: {LIGHT_TYPES}"

        light_data = bpy.data.lights.new(name=name, type=light_type)
        light_data.energy = intensity
        light_data.color = color

        light = bpy.data.objects.new(name=name, object_data=light_data)
        light.location = location
        bpy.context.collection.objects.link(light)

        return Light(light)

    @property
    def energy(self):
        """Energy of light source"""
        return self.obj.data.energy

    @energy.setter
    def energy(self, value):
        self.set_energy(value)

    @animatable_property("energy", "data")
    def set_energy(self, value: float):
        """Set energy of light source

        :param value: Energy of light source
        :return:
        """
        self.obj.data.energy = value

    @property
    def color(self):
        """Color of light source"""
        return self.obj.data.color

    @color.setter
    def color(self, value):
        self.set_color(value)

    @animatable_property("color", "data")
    def set_color(self, value: types.VectorLike):
        """Set color of light source

        :param value: RGB[A] color
        """
        self.obj.data.color = value
