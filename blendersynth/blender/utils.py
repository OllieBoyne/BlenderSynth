import bpy

class GetNewObject():
	def __init__(self, scene):
		self.scene = scene
		self.imported_obj = None

	def __enter__(self):
		self.old_objs = set(self.scene.objects)

	def __exit__(self, *args):
		x = set(self.scene.objects) - self.old_objs
		assert len(x) > 0, "No imported objects found..."

		if len(x) == 1:
			self.imported_obj = x.pop()

		else:

			# assume there is a hierarchy to the objects - get the highest
			parent_obj = None
			for obj in x:
				if obj.parent is None:
					parent_obj = obj
					break

			assert parent_obj is not None, "Multiple objects loaded,  but no parent object found..."

			self.imported_obj = parent_obj

def get_node_by_name(node_tree: bpy.types.NodeTree, key: str, raise_error=False):
	"""Given a nodetree and a key, return the first node found with label matching key"""
	for node in node_tree.nodes:
		if node.name == key:
			return node

	if raise_error:
		raise KeyError(f"Key {key} not found in node tree!\nLabels are: {[n.name for n in node_tree.nodes]}")