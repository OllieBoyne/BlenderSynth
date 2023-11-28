import bpy
from .nodes.node_arranger import tidy_tree
from typing import Union
from ..utils import io


class World:
    """World object - for managing world nodes, HDRIs, etc."""

    def __init__(self):
        self.mode = "Color"
        self.world = bpy.data.worlds["World"]
        self.node_tree = self.world.node_tree
        self.world_nodes = self.node_tree.nodes

        self.hdri_link = None
        self._setup_nodes()

        self.set_color((0.051,) * 3)  # match blender's default world color

    def _check_exists(self):
        """Node tree may have been wiped, eg by loading a new file.
        Check if the nodes exist, and if not, recreate them."""

        try:
            self.node_tree.rna_type
        except ReferenceError:
            self.__init__()

    def _setup_nodes(self):
        self._check_exists()
        nodes = self.world_nodes
        nodes.clear()

        self.node_texture = nodes.new(type="ShaderNodeTexEnvironment")
        self.node_background = nodes.new(type="ShaderNodeBackground")
        self.node_output = nodes.new(type="ShaderNodeOutputWorld")

        self.node_tree.links.new(
            self.node_background.outputs["Background"],
            self.node_output.inputs["Surface"],
        )

        tidy_tree(self.node_tree)

    def _setup_color(self):
        self._check_exists()
        if self.mode == "Color":
            return

        if self.hdri_link is not None:
            self.node_tree.links.remove(self.hdri_link)

        tidy_tree(self.node_tree)

        self.mode = "Color"

    def _setup_hdri(self):
        self._check_exists()
        if self.mode == "HDRI":
            return

        # Link the nodes
        self.hdri_link = self.node_tree.links.new(
            self.node_texture.outputs["Color"], self.node_background.inputs["Color"]
        )
        tidy_tree(self.node_tree)

        self.mode = "HDRI"

    def set_color(self, color: Union[list, tuple], affect_scene: bool = True):
        """Set the world color.

        :param color: RGB or RGBA color
        :param affect_scene: Toggle for whether color's lighting should affect the scene (if False, functions as a solid background color)
        """

        self._setup_color()

        assert len(color) in [3, 4], "Color must be RGB or RGBA"

        if len(color) == 3:
            color = (*color, 1.0)

        self.node_background.inputs["Color"].default_value = color
        self._lighting_from_background(affect_scene)

    def set_hdri(self, pth: str, affect_scene: bool = True, intensity: float = None):
        """Set the HDRI image location

        :param pth: Path to the HDRI image (.hdr or .exr)
        :param affect_scene: Toggle for whether color's lighting should affect the scene (if False, functions as a solid background color)
        :param intensity: [Optional] Set the intensity of the HDRI lighting"""

        self._setup_hdri()
        self.world_nodes["Environment Texture"].image = io.load_image(pth)
        self._lighting_from_background(affect_scene)

        if intensity:
            self.set_intensity(intensity)

    def set_intensity(self, intensity: float = 1.0):
        """Set the intensity of the color/HDRI.

        :param intensity: The intensity value
        """
        self.world_nodes["Background"].inputs[1].default_value = intensity

    def set_transparent(self, transparent=True):
        bpy.context.scene.render.film_transparent = transparent

    def _lighting_from_background(self, val=True):
        """Change the ability for the background to influence lighting on the scene"""
        self.world.cycles_visibility.diffuse = val


world = World()
