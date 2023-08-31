"""Create a custom AOV based on distance to cube."""

import blendersynth as bsyn

bsyn.run_this_script(debug=False)


class WorldPositionAOV(bsyn.aov.AOV):
	def _add_to_shader(self, shader_node_tree):
		# Define nodes to add
		geometry_node = shader_node_tree.nodes.new('ShaderNodeNewGeometry')
		map_range_node = shader_node_tree.nodes.new('ShaderNodeMapRange')

		# Set up map range node
		map_range_node.data_type = 'FLOAT_VECTOR'
		map_range_node.inputs[7].default_value = (-1, -1, -1)  # 'From Min'
		map_range_node.inputs[8].default_value = (1, 1, 1)  # 'From Max'

		# Link nodes
		shader_node_tree.links.new(geometry_node.outputs['Position'], map_range_node.inputs['Vector'])

		# Return output socket
		return map_range_node.outputs['Vector']


# create monkey and light
monkey = bsyn.Mesh.from_primitive('monkey', scale=2)
light = bsyn.Light.create('POINT', location=(0, -5, 0), intensity=100)

aov = WorldPositionAOV(name='WorldPosition')
monkey.assign_aov(aov)

# Set up render parameters
bsyn.render.set_resolution(256, 256)
bsyn.render.set_cycles_samples(10)

# Define outputs & render
comp = bsyn.Compositor(background_color=(1, 1, 1))
comp.define_output('Image', file_name='rgb', directory='custom_aov')
comp.define_output(aov, file_name='position', directory='custom_aov')
comp.render()
