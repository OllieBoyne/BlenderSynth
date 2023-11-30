# # Add mask node & Mix node
# mask_node = self.get_mask(mask_index)
# mix_node = self.node_tree.nodes.new('CompositorNodeMixRGB')
# mix_node.inputs[1].default_value = (0, 0, 0, 0)  # black - 0 alpha
#
# self.node_tree.links.new(mask_node.outputs['Alpha'], mix_node.inputs['Fac'])
# self.node_tree.links.new(self.render_layers_node.outputs[input_name], mix_node.inputs[2])
# self.node_tree.links.new(mix_node.outputs['Image'], node.inputs['Image'])

from ..nodes import CompositorNodeGroup


class MaskOverlay(CompositorNodeGroup):
    def __init__(self, name, node_tree, index=0, use_antialiasing=True, dtype="Color"):
        """
        Takes an IndexOB and an Image, and sets the values of all pixels with index != IndexOB
        to (0, 0, 0, 0)
        """

        super().__init__(name, node_tree)

        # define I/O
        self.add_socket("NodeSocketFloat", "IndexOB", "INPUT")
        self.add_socket(f"NodeSocket{dtype}", "Image", "INPUT")
        self.add_socket(f"NodeSocket{dtype}", "Image", "OUTPUT")

        # create nodes
        self.mask_node = self.group.nodes.new("CompositorNodeIDMask")
        self.mask_node.index = index
        self.mask_node.use_antialiasing = use_antialiasing

        self.mix_node = self.group.nodes.new("CompositorNodeMixRGB")
        self.mix_node.inputs[1].default_value = (0, 0, 0, 1)  # to set color to black

        self.alpha_node = self.group.nodes.new(
            "CompositorNodeSetAlpha"
        )  # to set alpha to 0
        self.alpha_node.mode = "APPLY"

        # link up internal nodes
        self.group.links.new(
            self.input_node.outputs["IndexOB"], self.mask_node.inputs["ID value"]
        )
        self.group.links.new(self.input_node.outputs["Image"], self.mix_node.inputs[2])
        self.group.links.new(
            self.mask_node.outputs["Alpha"], self.mix_node.inputs["Fac"]
        )
        self.group.links.new(
            self.mask_node.outputs["Alpha"], self.alpha_node.inputs["Alpha"]
        )
        self.group.links.new(
            self.mix_node.outputs["Image"], self.alpha_node.inputs["Image"]
        )
        self.group.links.new(
            self.alpha_node.outputs["Image"], self.output_node.inputs["Image"]
        )
