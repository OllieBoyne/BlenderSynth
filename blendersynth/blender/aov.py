"""Shader AOV manager"""

import bpy
from .nodes import tidy_tree, DeformedGeneratedTextureCoordinates, tree_add_socket
from ..utils import types
from typing import Union

ref_frames = ["CAMERA", "WORLD", "OBJECT"]

# Acceptable socket types for AOV colors & nodes
_socket_color_types = (bpy.types.NodeSocketVector, bpy.types.NodeSocketColor)
_socket_value_types = (bpy.types.NodeSocketFloat, bpy.types.NodeSocketInt)


# docs-special-members: __init__
# no-inherited-members


class AOV:
    """A generic Arbitrary Output Value.
    An AOV is a float or color value per-point that is calculated at the rendering stage,
    and can be output in a compositor to form an image.
    See `Blender docs <https://docs.blender.org/manual/en/latest/render/shader_nodes/output/aov.html>`_ for more info.
    """

    def __init__(self, *, name=None, **kwargs):
        if name is None:
            name = self.__class__.__name__

        self.name = name
        self._aov = None
        self._add_to_view_layer()

    def _add_to_view_layer(self, view_layer=None):
        """Add aov to view layer if not already there"""
        if view_layer is None:
            view_layer = bpy.context.view_layer

        for aov in view_layer.aovs:
            if aov.name == self.name:
                return

        aov = view_layer.aovs.add()
        aov.name = self.name
        self._aov = aov

    def add_to_shader(self, shader_node_tree):
        """Add AOV to shader node tree"""
        # add_to_shader must return output socket to connect to node
        out_socket = self._add_to_shader(shader_node_tree)

        # check node socket is correct type
        AOV_TYPE = None
        if isinstance(out_socket, _socket_color_types):
            AOV_TYPE = "COLOR"
        elif isinstance(out_socket, _socket_value_types):
            AOV_TYPE = "VALUE"
        else:
            raise ValueError(
                f"Output of _add_to_layer must be in {_socket_color_types} if Color or {_socket_value_types} if value. Got: `{type(out_socket)}`"
            )

        shader_aov_node = shader_node_tree.nodes.new("ShaderNodeOutputAOV")
        shader_aov_node.name = self.name
        shader_node_tree.links.new(out_socket, shader_aov_node.inputs[AOV_TYPE.title()])

        self._aov.type = AOV_TYPE
        tidy_tree(shader_node_tree)

    def _add_to_shader(self, shader_node_tree) -> bpy.types.NodeSocket:
        raise NotImplementedError

    def update(self):
        """Some AOVs need an update before rendering (to change certain node properties)"""
        return

    def __str__(self):
        return self.name


class NormalsAOV(AOV):
    def __init__(
        self,
        *,
        name: str = None,
        ref_frame: str = "CAMERA",
        order: str = "XYZ",
        polarity: Union[tuple, list] = (1, 1, 1),
    ):
        """Given a shader node tree, add surface normals as output.

        :param name: Name of AOV to add
        :param ref_frame: Reference frame to use for normals
        :param order: Order of components in RGB (default: XYZ)
        :param polarity: Polarity of XYZ (1 or -1)
        """
        super().__init__(name=name)
        assert ref_frame in ref_frames, f"ref_frame must be one of {ref_frames}"

        self.ref_frame = ref_frame
        self.order = order
        self.polarity = polarity

    def _add_to_shader(self, shader_node_tree):
        geom_node = shader_node_tree.nodes.new("ShaderNodeNewGeometry")
        vec_transform = shader_node_tree.nodes.new("ShaderNodeVectorTransform")
        map_range_node = shader_node_tree.nodes.new("ShaderNodeMapRange")

        vec_transform.vector_type = "NORMAL"
        vec_transform.convert_to = self.ref_frame

        # Set up mapping - with polarity
        map_range_node.data_type = "FLOAT_VECTOR"
        for i in range(3):
            map_range_node.inputs[7].default_value[i] = -self.polarity[i]
            map_range_node.inputs[8].default_value[i] = self.polarity[i]

        # Set up ordering
        sep_xyz_node = shader_node_tree.nodes.new("ShaderNodeSeparateXYZ")
        comb_xyz_node = shader_node_tree.nodes.new("ShaderNodeCombineXYZ")
        for i in range(3):
            shader_node_tree.links.new(
                sep_xyz_node.outputs[self.order[i]], comb_xyz_node.inputs["XYZ"[i]]
            )

        # Make necessary connections for shader graph
        shader_node_tree.links.new(
            geom_node.outputs["True Normal"], vec_transform.inputs["Vector"]
        )
        shader_node_tree.links.new(
            vec_transform.outputs["Vector"], map_range_node.inputs["Vector"]
        )
        shader_node_tree.links.new(
            map_range_node.outputs["Vector"], sep_xyz_node.inputs["Vector"]
        )

        return comb_xyz_node.outputs["Vector"]


class GeneratedAOV(AOV):
    """'Generated Texture Coordinates'.

    These are coordinates normalized to 0-1 for the object's undeformed bounding box, not taking into account
    deformation (pose, modifiers). See `Blender docs <https://docs.blender.org/manual/en/latest/render/shader_nodes/input/texture_coordinate.html>`_ for more info.
    """

    def _add_to_shader(self, shader_node_tree):
        texcon_node = shader_node_tree.nodes.new("ShaderNodeTexCoord")
        return texcon_node.outputs["Generated"]


class DisplacementGeneratedAOV(AOV):
    """In the same co-ordinate space as :class:`GeneratedAOV`, give the displacement vector
    for each point under modifiers (e.g. pose).

    By default, this deformation is mapped from the range [-1 to 1] to [0 to 1], with 0.5 representing no
    deformation. Any values outside of this range are clamped.
    This can be modified through the input kwargs vmin and vmax.
    """

    def __init__(
        self,
        *,
        name: str = None,
        mesh: types.Mesh = None,
        bbox_min: types.VectorLike = None,
        bbox_max: types.VectorLike = None,
        vmin: float = -1,
        vmax: float = 1,
    ):
        """Create AOV for displacement under modifiers.

        :param name: Name of AOV
        :param mesh: Mesh to calculate bounds for. Will be used to find bbox_min and bbox_max if given
        :param bbox_min: Minimum of bounding box. If not given, calculated from Mesh
        :param bbox_max: Maximum of bounding box. If not given, calculated from Mesh
        :param vmin: Minimum deformation to map to 0
        :param vmax: Maximum value to map to 1
        """

        super().__init__(name=name)
        self.mesh = mesh
        self.bbox_min = bbox_min
        self.bbox_max = bbox_max
        self.vmin = vmin
        self.vmax = vmax

        assert mesh is not None or (
            bbox_min is not None and bbox_max is not None
        ), "Either mesh or bbox_min and bbox_max must be given for DisplacementGeneratedAOV"

    def _add_to_shader(self, shader_node_tree):
        self.deformed_coords = DeformedGeneratedTextureCoordinates(
            node_tree=shader_node_tree,
            mesh=self.mesh,
            bbox_min=self.bbox_min,
            bbox_max=self.bbox_max,
        )

        self.generated_coords = shader_node_tree.nodes.new("ShaderNodeTexCoord")

        # subtract one from the other
        sub_node = shader_node_tree.nodes.new("ShaderNodeVectorMath")
        sub_node.operation = "SUBTRACT"

        # map result to range 0-1
        map_range_node = shader_node_tree.nodes.new("ShaderNodeMapRange")
        map_range_node.data_type = "FLOAT_VECTOR"
        map_range_node.inputs[7].default_value = [self.vmin] * 3
        map_range_node.inputs[8].default_value = [self.vmax] * 3

        # link up nodes
        shader_node_tree.links.new(
            self.deformed_coords.outputs["Vector"], sub_node.inputs[0]
        )
        shader_node_tree.links.new(
            self.generated_coords.outputs["Generated"], sub_node.inputs[1]
        )
        shader_node_tree.links.new(
            sub_node.outputs["Vector"], map_range_node.inputs["Vector"]
        )

        tidy_tree(shader_node_tree)
        return map_range_node.outputs["Vector"]

    def set_bounds(
        self,
        mesh: types.Mesh = None,
        bbox_min: types.VectorLike = None,
        bbox_max: types.VectorLike = None,
    ):
        """Set bounds for DeformedGeneratedTextureCoordinates node group

        :param mesh: Mesh to calculate bounds for. Will be used to find bbox_min and bbox_max if given
        :param bbox_min: Minimum of bounding box. If not given, calculated from Mesh
        :param bbox_max: Maximum of bounding box. If not given, calculated from Mesh
        """
        self.mesh = mesh
        self.bbox_min = bbox_min
        self.bbox_max = bbox_max
        self.node_group.register_bounds(mesh, bbox_min, bbox_max)


class UVAOV(AOV):
    """UV coordinates. See `Blender docs <https://docs.blender.org/manual/en/latest/editors/uv/index.html#editors-uv-index>`_ for more info."""

    def _add_to_shader(self, shader_node_tree):
        texcon_node = shader_node_tree.nodes.new("ShaderNodeTexCoord")
        return texcon_node.outputs["UV"]


class ValueAOV(AOV):
    """A generic AOV that outputs a single value"""

    def __init__(self, value: float = 0, name=None, **kwargs):
        """
        :param value: Value to output
        :param name: Name of AOV
        :param kwargs: Additional kwargs to pass to :class:`AOV`
        """

        super().__init__(name=name, **kwargs)
        self._value = 0
        self.value_node = None

        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        if self.value_node is not None:
            self.value_node.outputs["Value"].default_value = value

    def _add_to_shader(self, shader_node_tree):
        self.value_node = shader_node_tree.nodes.new("ShaderNodeValue")
        self.value = self._value
        return self.value_node.outputs["Value"]


class AttrAOV(AOV):
    """Take an object attribute, and output it as an AOV"""

    attribute_type = None
    attribute_name = None

    def _add_to_shader(self, shader_node_tree):
        attr_node = shader_node_tree.nodes.new("ShaderNodeAttribute")
        attr_node.attribute_type = self.attribute_type
        attr_node.attribute_name = self.attribute_name
        return attr_node.outputs["Fac"]


class InstanceIDAOV(AttrAOV):
    """Instance ID - given to each object on creation.
    Output is an integer corresponding to the object's instance ID (0-indexed)
    """

    attribute_type = "OBJECT"
    attribute_name = "instance_id"


class ClassIDAOV(AttrAOV):
    """Class ID - given to each object on creation.
    Output is an integer corresponding to the object's class ID (0-indexed)
    Class IDs can be manually set either when creating a Mesh, or by using the Mesh's :meth:`~blendersynth.blender.mesh.Mesh.set_class_id` method.
    If not set, will default to a different index from each primitive.
    """

    attribute_type = "OBJECT"
    attribute_name = "class_id"


class AttrRGBAOV(AOV):
    """
    For a given numerical attribute, outputs a color corresponding to the attribute's value.
    Object with attribute value `i` has HSV color `(i/N, 1, 1)`.
    `N` can be a property of the object to update.
    Runs :meth:`~update()` method to change the value of `N`, which is called before rendering.
    """

    attribute_type = None
    attribute_name = None

    def __init__(self, *, name=None):
        super().__init__(name=name)

        # Create Int Index -> HSV as a node group, so the 'num_objects' parameter can be edited centrally
        self.group = bpy.data.node_groups.new(name="IdxToHue", type="ShaderNodeTree")

        tree_add_socket(self.group, "NodeSocketFloat", "Index", "INPUT")
        tree_add_socket(self.group, "NodeSocketColor", "Color", "OUTPUT")

        self.input_node = self.group.nodes.new("NodeGroupInput")
        self.output_node = self.group.nodes.new("NodeGroupOutput")

        self.div_node = div_node = self.group.nodes.new(
            "ShaderNodeMath"
        )  # Need to keep reference so can update at runtime
        div_node.operation = "DIVIDE"
        div_node.use_clamp = True
        div_node.inputs[1].default_value = self.N

        hsv_node = self.group.nodes.new("ShaderNodeHueSaturation")
        hsv_node.inputs["Saturation"].default_value = 1
        hsv_node.inputs["Value"].default_value = 1
        hsv_node.inputs["Color"].default_value = (1, 0, 0, 1)  # Red

        self.group.links.new(self.input_node.outputs["Index"], div_node.inputs[0])
        self.group.links.new(div_node.outputs["Value"], hsv_node.inputs["Hue"])
        self.group.links.new(
            hsv_node.outputs["Color"], self.output_node.inputs["Color"]
        )
        tidy_tree(self.group)

    def _add_to_shader(self, shader_node_tree):
        attr_node = shader_node_tree.nodes.new("ShaderNodeAttribute")
        attr_node.attribute_type = self.attribute_type
        attr_node.attribute_name = self.attribute_name

        # Create a group node for the Int Index -> HSV conversion
        group_node = shader_node_tree.nodes.new("ShaderNodeGroup")
        group_node.node_tree = self.group

        shader_node_tree.links.new(attr_node.outputs["Fac"], group_node.inputs["Index"])
        return group_node.outputs["Color"]

    def update(self):
        self.div_node.inputs[1].default_value = self.N

    @property
    def N(self):
        return 0


class InstanceRGBAOV(AttrRGBAOV):
    """
    :class:`~InstanceIDAOV` as an :class:`~AttrRGBAOV` for visualisation.
    Updates `N` at render time by reading the scene property 'NUM_MESHES'
    """

    attribute_type = "OBJECT"
    attribute_name = "instance_id"

    @property
    def N(self):
        """Total number of meshes in the scene"""
        return bpy.context.scene.get("NUM_MESHES", 0) + 1


class ClassRGBAOV(AttrRGBAOV):
    """
    :class:`~ClassIDAOV` but as an :class:`~AttrRGBAOV` for visualisation.
    Updates `N` at render time by reading the scene property `MAX_CLASSES`
    """

    attribute_type = "OBJECT"
    attribute_name = "class_id"

    @property
    def N(self):
        """Update the divisor node with the current number of classes"""
        return bpy.context.scene.get("MAX_CLASSES", 0) + 1
