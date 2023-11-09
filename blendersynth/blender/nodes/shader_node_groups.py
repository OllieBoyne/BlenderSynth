"""Node Group collections for use in Blender"""

import bpy
from ...utils import types
import numpy as np
from mathutils import Vector
from .node_group import ShaderNodeGroup

# docs-special-members: __init__
# no-inherited-members


class DeformedGeneratedTextureCoordinates(ShaderNodeGroup):
    """
    A :class:`ShaderNodeGroup` that outputs generated texture coordinates, but in the deformed space.

    For example use, see :class:`DisplacementGeneratedAOV <blendersynth.blender.aov.DisplacementGeneratedAOV>`.
    """

    def __init__(
        self,
        node_tree: bpy.types.NodeTree,
        mesh: types.Mesh,
        bbox_min: types.VectorLike,
        bbox_max: types.VectorLike,
    ):
        """To calculate the generated space, either needs mesh or bbox_min, bbox_max.

        :param node_tree: NodeTree to add group to
        :param mesh: If given, `bbox_min` and `bbox_max` are calculated using this
        :param bbox_min: If given, `bbox_max` must also be given. The minimum of the bounding box of the mesh
        :param bbox_max: If given, `bbox_min` must also be given. The maximum of the bounding box of the mesh
        """

        super().__init__("DeformedGeneratedTextureCoordinates", node_tree)

        self.group.outputs.new("NodeSocketVector", "Vector")

        self.geometry_node = self.add_node("ShaderNodeNewGeometry")
        self.vec_transform_node = self.add_node("ShaderNodeVectorTransform")
        self.map_range_node = self.add_node("ShaderNodeMapRange")

        self.vec_transform_node.vector_type = "POINT"
        self.vec_transform_node.convert_from = "WORLD"
        self.vec_transform_node.convert_to = "OBJECT"

        self.map_range_node.clamp = False  # avoid clamping to 0-1
        self.map_range_node.data_type = "FLOAT_VECTOR"
        self.register_bounds(mesh, bbox_min, bbox_max)

        # link everything up
        self.link(
            self.geometry_node.outputs["Position"],
            self.vec_transform_node.inputs["Vector"],
        )
        self.link(
            self.vec_transform_node.outputs["Vector"],
            self.map_range_node.inputs["Vector"],
        )
        self.link(
            self.map_range_node.outputs["Vector"], self.output_node.inputs["Vector"]
        )

        self.tidy()

    def register_bounds(
        self, mesh: types.Mesh, bbox_min: types.VectorLike, bbox_max: types.VectorLike
    ):
        # calculate bbox_min, bbox_max if not given
        if mesh:
            bbox_min, bbox_max = mesh.get_raw_bounds()

        self.map_range_node.inputs[7].default_value = bbox_min
        self.map_range_node.inputs[8].default_value = bbox_max
