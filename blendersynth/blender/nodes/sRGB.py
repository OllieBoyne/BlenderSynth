"""Compositor node groups for converting sRGB to linear RGB."""

import bpy
from .node_arranger import tidy_tree
from .node_group import tree_add_socket

_srgb_to_linear_single_value_name = "sRGB to Linear Value"
_srgb_to_linear_name = "sRGB to Linear"

def _srgb_to_linear_single_value() -> bpy.types.CompositorNodeGroup:
    """Create node group to go from a single value, sRGB to linear RGB."""

    if _srgb_to_linear_single_value_name in bpy.data.node_groups:
        return bpy.data.node_groups[_srgb_to_linear_single_value_name]

    group = bpy.data.node_groups.new(type="CompositorNodeTree", name=_srgb_to_linear_single_value_name)

    nodes = group.nodes
    input_node = group.nodes.new("NodeGroupInput")
    output_node = group.nodes.new("NodeGroupOutput")

    tree_add_socket(group, "NodeSocketFloat", "sRGB", "INPUT")
    tree_add_socket(group, "NodeSocketFloat", "Linear", "OUTPUT")

    # If sRGB < 0.04045, then Linear = sRGB / 12.92
    # Else, Linear = ((sRGB + 0.055) / 1.055) ^ 2.4

    linear_mode = nodes.new("CompositorNodeMath")
    linear_mode.operation = "DIVIDE"
    linear_mode.inputs[1].default_value = 12.92

    nonlinear_1 = nodes.new("CompositorNodeMath")
    nonlinear_1.operation = "ADD"
    nonlinear_1.inputs[1].default_value = 0.055

    nonlinear_2 = nodes.new("CompositorNodeMath")
    nonlinear_2.operation = "DIVIDE"
    nonlinear_2.inputs[1].default_value = 1.055

    nonlinear_3 = nodes.new("CompositorNodeMath")
    nonlinear_3.operation = "POWER"
    nonlinear_3.inputs[1].default_value = 2.4

    choose_region_node = nodes.new("CompositorNodeMath")
    choose_region_node.operation = "LESS_THAN"
    choose_region_node.inputs[1].default_value = 0.04045

    switch_node = nodes.new("CompositorNodeMixRGB")

    links = group.links

    links.new(input_node.outputs[0], choose_region_node.inputs[0])
    links.new(choose_region_node.outputs[0], switch_node.inputs[0])

    links.new(input_node.outputs[0], nonlinear_1.inputs[0])
    links.new(nonlinear_1.outputs[0], nonlinear_2.inputs[0])
    links.new(nonlinear_2.outputs[0], nonlinear_3.inputs[0])
    links.new(nonlinear_3.outputs[0], switch_node.inputs[1])

    links.new(input_node.outputs[0], linear_mode.inputs[0])
    links.new(linear_mode.outputs[0], switch_node.inputs[2])

    links.new(switch_node.outputs[0], output_node.inputs[0])

    tidy_tree(group)
    return group

def srgb_to_linear() -> bpy.types.CompositorNodeGroup:

    if _srgb_to_linear_name in bpy.data.node_groups:
        return bpy.data.node_groups[_srgb_to_linear_name]

    single_value_group = _srgb_to_linear_single_value()

    group = bpy.data.node_groups.new(type="CompositorNodeTree", name=_srgb_to_linear_name)
    nodes = group.nodes

    input_node = group.nodes.new("NodeGroupInput")
    output_node = group.nodes.new("NodeGroupOutput")

    # Split to colour, then pass each colour through instance of srgb_to_linear, then combine and output.
    tree_add_socket(group, "NodeSocketColor", "sRGB", "INPUT")
    tree_add_socket(group, "NodeSocketColor", "Linear", "OUTPUT")

    splitter = nodes.new("CompositorNodeSepRGBA")
    combiner = nodes.new("CompositorNodeCombRGBA")

    convert_R = nodes.new(type="CompositorNodeGroup")
    convert_G = nodes.new(type="CompositorNodeGroup")
    convert_B = nodes.new(type="CompositorNodeGroup")

    convert_R.node_tree = single_value_group
    convert_G.node_tree = single_value_group
    convert_B.node_tree = single_value_group

    links = group.links
    links.new(input_node.outputs[0], splitter.inputs[0])
    links.new(splitter.outputs[0], convert_R.inputs[0])
    links.new(splitter.outputs[1], convert_G.inputs[0])
    links.new(splitter.outputs[2], convert_B.inputs[0])

    links.new(convert_R.outputs[0], combiner.inputs[0])
    links.new(convert_G.outputs[0], combiner.inputs[1])
    links.new(convert_B.outputs[0], combiner.inputs[2])

    links.new(splitter.outputs[3], combiner.inputs[3]) # Alpha unchanged.

    links.new(combiner.outputs[0], output_node.inputs[0])

    tidy_tree(group)
    return group


