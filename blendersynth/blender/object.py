import os.path

import bpy
from blender.utils import GetNewObject
from blender.aov import AOV

_primitives ={
	"cube": bpy.ops.mesh.primitive_cube_add,
	"sphere": bpy.ops.mesh.primitive_uv_sphere_add,
	"cylinder": bpy.ops.mesh.primitive_cylinder_add,
	"plane": bpy.ops.mesh.primitive_plane_add,
	"cone": bpy.ops.mesh.primitive_cone_add,
	"monkey": bpy.ops.mesh.primitive_monkey_add
}

class BSObject:
	def __init__(self, obj, material=None):
		self.obj = obj

		# Must have a material, create if not passed
		if material is None:
			material = bpy.data.materials.new(name='Material')
			material.use_nodes = True
		self.obj.data.materials.append(material)

	@classmethod
	def from_primitive(cls, name='cube'):
		"""Create object from primitive"""
		assert name in _primitives, f"Primitive `{name}` not found. Options are: {list(_primitives.keys())}"

		importer = GetNewObject(bpy.context.scene)
		with importer:
			prim = _primitives[name]()  # Create primitive
		return cls(importer.imported_obj)  # Return object

	@classmethod
	def from_obj(cls, obj_loc):
		"""Load object from .obj file"""
		assert os.path.isfile(obj_loc) and obj_loc.endswith('.obj'), f"File `{obj_loc}` not a valid .obj file"

		directory, fname = os.path.split(obj_loc)

		importer = GetNewObject(bpy.context.scene)
		with importer:
			bpy.ops.import_scene.obj(filepath=fname, directory=directory, filter_image=True,
									 files=[{"name": fname}], forward_axis='X', up_axis='Z')

		return cls(importer.imported_obj)

	@property
	def materials(self):
		return self.obj.data.materials

	def assign_aov(self, aov: AOV):
		"""Assign AOV to object.
		Requires exactly 1 material on object."""
		assert len(self.materials) == 1, f"Object must have exactly 1 material. Found {len(self.materials)}"

		shader_node_tree = self.materials[0].node_tree
		assert shader_node_tree is not None, "Material must have a node tree"
		aov.add_to_shader(shader_node_tree)

	def set_euler_rotation(self, x, y, z):
		self.obj.rotation_euler = (x, y, z)

	def set_position(self, x, y, z):
		self.obj.location = (x, y, z)