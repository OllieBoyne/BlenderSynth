"""Utilities for neatly arranging nodes in the node editor,
to make debugging easier."""

import bpy
from collections import defaultdict
from copy import copy


def get_source_nodes(node):
    for i in node.inputs:
        for link in i.links:
            yield link.from_node


def get_sink_nodes(node):
    for o in node.outputs:
        for link in o.links:
            yield link.to_node


def split_to_islands(nodes):
    """Given a node list, return a list of sets, each one being a fully disconnected island"""

    def dfs(node, island):
        """Depth-first search from node."""
        node["visited"] = True
        islands[node] = island
        for linked_node in [*get_source_nodes(node), *get_sink_nodes(node)]:
            if not linked_node["visited"]:
                dfs(linked_node, island)

    islands = {}
    island_counter = 0

    # Set all nodes to unvisited
    for node in nodes:
        node["visited"] = False

    # Start a DFS from each unvisited node
    for node in nodes:
        if not node["visited"]:
            dfs(node, island_counter)
            island_counter += 1

    # Group nodes by island
    grouped_islands = []
    for i in range(island_counter):
        grouped_islands.append({k for k, v in islands.items() if v == i})

    return grouped_islands


def calc_depth(node_island):
    """Given a node island (i.e. all nodes in the same fully connected component),
    set the depth of each node to be the maximum depth of all its input nodes + 1.
    Once complete, normalize these depths so the first item is 0"""

    for nodes in node_island:
        nodes["depth"] = None

    node_island_copy = copy(node_island)
    start_node = node_island_copy.pop()
    start_node["depth"] = 0
    nodes_to_use = {start_node}

    # First Pass - assign a depth to each node by traversing the graph from the start node
    while any(node["depth"] is None for node in node_island):
        node = nodes_to_use.pop()
        for sink_node in get_sink_nodes(node):
            if sink_node in node_island:
                if sink_node["depth"] is None:
                    sink_node["depth"] = node["depth"] + 1
                    nodes_to_use.add(sink_node)

        for source_node in get_source_nodes(node):
            if source_node in node_island:
                if source_node["depth"] is None:
                    source_node["depth"] = node["depth"] - 1
                    nodes_to_use.add(source_node)

    # Second Pass - set each depth to be the maximum depth of all its input nodes + 1
    depth_changed = True
    while depth_changed:
        depth_changed = False
        for node in node_island:
            sources = [s for s in get_source_nodes(node) if s in node_island]
            if sources:
                new_depth = max(node["depth"] for node in sources) + 1
                if node["depth"] != new_depth:
                    node["depth"] = new_depth
                    depth_changed = True

    # Normalize depths
    min_depth = min(node["depth"] for node in node_island)
    for node in node_island:
        node["depth"] -= min_depth

    return node_island


def tidy_tree(node_tree: bpy.types.NodeTree, dX: int = 400, dY: int = 200):
    """Search through tree, positioning nodes in a grid based on their depth and connectivity.

    :param node_tree: node tree to tidy
    :param dX: horizontal distance between nodes
    :param dY: vertical distance between nodes"""

    nodes = node_tree.nodes
    islands = split_to_islands(nodes)

    y = 0  # track running height to manage multiple islands

    height = defaultdict(int)  # track height of each depth level
    for island in islands:
        island = calc_depth(island)

        # want to center each depth level, so set heights accordingly
        for i in range(max(node["depth"] for node in island) + 1):
            # Adjusting the initial height calculation to account for node sizes.
            depth_nodes = [node for node in island if node["depth"] == i]
            total_height_for_depth = sum(node.dimensions.y for node in depth_nodes)
            spacing_needed = dY * (len(depth_nodes) - 1)
            height[i] = -(total_height_for_depth + spacing_needed) / 2

        for node in island:
            node.location = (node["depth"] * dX, y + height[node["depth"]])
            height[node["depth"]] += (
                node.dimensions.y + dY
            )  # Incrementing by the node's height

        y += max(height.values()) + dY
