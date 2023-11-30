from ..nodes import CompositorNodeGroup
import bpy


class DepthVis(CompositorNodeGroup):
    def __init__(self, node_tree, max_depth=1, col=(1, 1, 1)):
        super().__init__(name="DepthVis", node_tree=node_tree)
        self.max_depth = 1

        self.add_socket("NodeSocketFloat", "Depth", "INPUT")
        self.add_socket("NodeSocketColor", "Image", "OUTPUT")

        self.map_range_node = self.group.nodes.new("CompositorNodeMapRange")
        self.map_range_node.inputs["From Max"].default_value = max_depth

        self.rgb_node = self.group.nodes.new("CompositorNodeRGB")
        if len(col) == 3:
            col = (*col, 1)

        self.rgb_node.outputs["RGBA"].default_value = col

        self.multiple_node = self.group.nodes.new("CompositorNodeMath")
        self.multiple_node.operation = "MULTIPLY"

        self.group.links.new(
            self.input_node.outputs["Depth"], self.map_range_node.inputs["Value"]
        )
        self.group.links.new(
            self.map_range_node.outputs["Value"], self.multiple_node.inputs[0]
        )
        self.group.links.new(
            self.rgb_node.outputs["RGBA"], self.multiple_node.inputs[1]
        )
        self.group.links.new(
            self.multiple_node.outputs["Value"], self.output_node.inputs["Image"]
        )

        self.tidy()
