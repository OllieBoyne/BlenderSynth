import bpy
from .bsyn_object import BsynObject
from .nodes import tidy_tree
from ..utils import io
from ..utils import version


def _new_shader_node(node_tree, node_type):
    shader_node = node_tree.nodes.new(type=node_type)
    if node_type == "ShaderNodeBsdfPrincipled":
        spec_key = "Specular IOR Level" if version.is_version_plus(4) else "Specular"
        shader_node.inputs[spec_key].default_value = 0

    return shader_node


class Material(BsynObject):
    """BlenderSynth Material class. Will always be a node material."""

    def __init__(
        self, name="NewMaterial", shader_type="ShaderNodeBsdfPrincipled", mat=None
    ):
        if mat is None:
            mat = bpy.data.materials.new(name)
            mat.use_nodes = True
            mat.node_tree.nodes.clear()
            self.shader = _new_shader_node(mat.node_tree, shader_type)
            self.output = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
            mat.node_tree.links.new(
                self.shader.outputs[0], self.output.inputs["Surface"]
            )

        else:
            self.shader = None
            self.output = mat.node_tree.nodes["Material Output"]

        mat.use_nodes = True
        self._object = mat

        self.node_tree = mat.node_tree
        self.nodes = self.node_tree.nodes
        self.links = self.node_tree.links

        self._image_nodes = {}  # dict of shader input socket : image node

        # set-up scaling
        self._add_scaling_node()
        self._scale = 1

        tidy_tree(self.node_tree)

    @classmethod
    def from_image(
        cls,
        image_loc,
        name="ImageMaterials",
        shader_type="ShaderNodeBsdfPrincipled",
        use_global_scale=True,
    ) -> "Material":
        """
        Create a new material from an image texture.
        :param image_loc: Location of the image
        :param name: Name of the material
        :param shader_type: Shader type
        :param use_global_scale: Flag to scale the image texture node by the global scale
        :return: New Material instance
        """
        mat = cls(name, shader_type=shader_type)  # new instance
        mat.add_source(
            image_loc, input_name="Base Color", use_global_scale=use_global_scale
        )

        return mat

    def add_source(
        self,
        image_loc: str,
        input_name: str = "Base Color",
        use_global_scale: bool = True,
        allow_duplicate: bool = False,
    ):
        """
        Add an image texture node to the material node tree, and connect it to the specified input of the Shader.
        :param image_loc: Image location
        :param input_name: Input socket name of the Shader to connect the image texture node to
        :param use_global_scale: Flag to scale the image texture node by the global scale
        :param allow_duplicate: Flag to allow duplicate image texture nodes (by default, a node to the same input will overwrite any previous)
        :return:
        """
        # Get the nodes in the material node tree
        nodes = self.obj.node_tree.nodes
        links = self.obj.node_tree.links

        # Find the Principled BSDF
        principled = next(
            (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
        )
        if not principled:
            raise ValueError(
                "add_source requires a Principled BSDF node in the material node tree"
            )

        if input_name in self._image_nodes and not allow_duplicate:
            tex_image_node = self._image_nodes[input_name]
        else:
            tex_image_node = nodes.new("ShaderNodeTexImage")

        tex_image_node.image = io.load_image(image_loc)
        self._image_nodes[input_name] = tex_image_node

        if input_name == "Displacement":
            # Connect to the 'Displacement' socket of the output node
            links.new(
                tex_image_node.outputs["Color"], self.output.inputs["Displacement"]
            )

        else:
            # Connect the image texture node to the specified input of the Principled BSDF
            links.new(tex_image_node.outputs["Color"], principled.inputs[input_name])

        if use_global_scale:
            links.new(self._texture_scaling_socket, tex_image_node.inputs["Vector"])

        if "color" not in input_name.lower():
            tex_image_node.image.colorspace_settings.name = "Non-Color"

        tidy_tree(self.node_tree)

    @classmethod
    def from_blender_material(cls, blender_mat: bpy.types.Material):
        if not isinstance(blender_mat, bpy.types.Material):
            raise ValueError("Invalid Blender material")

        # Create a new Material instance
        mat = cls(blender_mat.name, mat=blender_mat)

        # Find the shader and output nodes in the copied node tree
        mat.shader = next(
            (node for node in mat.nodes if node.type == "BSDF_PRINCIPLED"), None
        )
        mat.output = next(
            (node for node in mat.nodes if node.type == "OUTPUT_MATERIAL"), None
        )

        return mat

    def _add_scaling_node(self):
        """Add scaling node to the material node tree"""

        self.scale_node = self.nodes.new("ShaderNodeValue")
        tex_coord_node = self.nodes.new("ShaderNodeTexCoord")

        mapping_node = self.nodes.new("ShaderNodeMapping")

        self.links.new(self.scale_node.outputs[0], mapping_node.inputs["Scale"])
        self.links.new(tex_coord_node.outputs["UV"], mapping_node.inputs["Vector"])
        self._texture_scaling_socket = mapping_node.outputs["Vector"]

    def set_bdsf_property(self, key: str, value: float):
        """Set the property of the BSDF node"""
        if self.shader.type != "BSDF_PRINCIPLED":
            raise ValueError("Shader is not a Principled BSDF")

        if key not in self.shader.inputs:
            raise ValueError(f"Invalid BDSF shader property `{key}`")

        self.shader.inputs[key].default_value = value

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.scale_node.outputs[0].default_value = value

    @property
    def name(self):
        return self.obj.name
