import os.path

import bpy
from .utils import (
    GetNewObject,
    SelectObjects,
    handle_vec,
    CursorAt,
    animatable_property,
)
from .bsyn_object import BsynObject
from .material import Material
from .armature import Armature
from .aov import AOV
import numpy as np
import mathutils
import bmesh
from mathutils import Vector, Euler
from typing import Union, List
from copy import deepcopy
from ..utils import types

_primitives = {
    "cube": bpy.ops.mesh.primitive_cube_add,
    "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
    "cylinder": bpy.ops.mesh.primitive_cylinder_add,
    "plane": bpy.ops.mesh.primitive_plane_add,
    "cone": bpy.ops.mesh.primitive_cone_add,
    "monkey": bpy.ops.mesh.primitive_monkey_add,
    "torus": bpy.ops.mesh.primitive_torus_add,
}

default_ids = {
    "loaded_mesh": 0,
    "prim_cube": 1,
    "prim_sphere": 2,
    "prim_cylinder": 3,
    "prim_plane": 4,
    "prim_cone": 5,
    "prim_monkey": 6,
    "prim_torus": 7,
}


def _get_child_meshes(obj):
    """Given an object, return all meshes that are children of it. Recursively searches children of children.
    Also returns any child objects that aren't meshes"""
    if obj.type == "MESH":
        return [obj], []
    else:
        meshes, other = [], [obj]
        for child in obj.children:
            child_meshes, child_other = _get_child_meshes(child)
            meshes += child_meshes
            other += child_other

        return meshes, other


def _set_object_origin(obj: bpy.types.Object, origin: Vector):
    """Set the origin of an object to a given point"""
    with SelectObjects([obj]), CursorAt(origin):
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")


def _find_material(obj):
    """Return first material found in an object"""
    if obj.type == "MESH":
        for mat in obj.data.materials:
            return mat

    for child in obj.children:
        if child.type == "MESH":
            for mat in child.data.materials:
                return mat


class Mesh(BsynObject):
    """A mesh object. Can be a single mesh, or a hierarchy of meshes."""

    primitive_list = list(_primitives.keys())
    """List of available primitives"""

    def __init__(
        self,
        obj,
        material: bpy.types.Material = None,
        scene: bpy.types.Scene = None,
        class_id: int = None,
    ):
        """
        :param obj: Receives either a single mesh, or an empty with children empty & meshes
        :param material: bpy.types.Material to assign to the mesh
        :param scene:

        If obj contains multiple meshes, they will all be assigned the same material, and must act as a single object
        i.e. they will all be transformed together

        """

        if scene is None:
            scene = bpy.context.scene

        self.scene = scene
        self._object = obj
        self._meshes, self._other_objects = _get_child_meshes(obj)

        # Manage materials here
        if material is not None:
            self._material = Material.from_blender_material(material)
        elif _find_material(obj) is not None:
            self._material = Material.from_blender_material(_find_material(obj))
        else:
            self._material = Material("NewMaterial")

        for mesh in self._meshes:
            mesh.data.materials.append(self._material.object)

        # INSTANCING - Define InstanceID based on number of meshes in scene
        self._object["instance_id"] = scene.get("NUM_MESHES", 0)
        scene["NUM_MESHES"] = (
            scene.get("NUM_MESHES", 0) + 1
        )  # Increment number of meshes in scene

        # CLASS - Define class based on type of object (e.g. primitive)
        # can be overriden at any point
        self.set_class_id(class_id)

        self.assigned_aovs = []
        self._armatures = (
            {}
        )  # name : armature, to prevent multiple instances of armatures

    def set_class_id(self, class_id: int):
        """Set the class ID of the object.

        :param class_id: Class ID to assign to object
        """

        assert isinstance(
            class_id, int
        ), f"Class ID must be an integer, not {type(class_id)}"
        assert class_id >= 0, f"Class ID must be >= 0, not {class_id}"

        self._object["class_id"] = class_id
        self.scene["MAX_CLASSES"] = max(self.scene.get("MAX_CLASSES", 0), class_id)

    @classmethod
    def from_scene(cls, key: str, class_id: int = 0) -> "Mesh":
        """Create object from named object in scene.

        :param key: Name of object in scene
        :param class_id: Class ID to assign to object

        :return: Mesh loaded from scene"""
        obj = bpy.data.objects[key]
        return cls(obj, class_id=class_id)

    @classmethod
    def from_primitive(
        cls,
        name="cube",
        scale=None,
        location=None,
        rotation_euler=None,
        class_id=None,
        **kwargs,
    ) -> "Mesh":
        """Create Mesh from primitive.

        :param name: Name of primitive to create. See :attr:`~blendersynth.blender.Mesh.primitive_list` for options
        :param scale: Scale of object
        :param location: Location of object
        :param rotation_euler: Rotation of object
        :param class_id: Class ID to assign to object
        :param kwargs: Additional arguments to pass to primitive (see `bpy.ops.mesh.primitive_cube_add <https://docs.blender.org/api/current/bpy.ops.mesh.html#bpy.ops.mesh.primitive_cube_add>`_, etc.)

        :return: Mesh object created from primitive
        """

        assert (
            name in _primitives
        ), f"Primitive `{name}` not found. Options are: {list(_primitives.keys())}"

        importer = GetNewObject(bpy.context.scene)
        with importer:
            prim = _primitives[name](**kwargs)  # Create primitive

        if class_id is None:
            class_id = default_ids[f"prim_{name}"]

        obj = cls(importer.imported_obj, class_id=class_id)

        if scale is not None:
            obj.scale = scale
        if location is not None:
            obj.location = location
        if rotation_euler is not None:
            obj.rotation_euler = rotation_euler

        return obj

    @classmethod
    def from_numpy(
        cls, vertices: np.ndarray, faces: np.ndarray, name="New_Mesh"
    ) -> "Mesh":
        """Create Mesh from numpy arrays of vertices and faces."""
        mesh = bpy.data.meshes.new(name=name)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        mesh.from_pydata(vertices.tolist(), [], faces.tolist())
        mesh.update()

        return cls(obj, class_id=default_ids["loaded_mesh"])

    @classmethod
    def from_obj(
        cls,
        obj_loc: str,
        class_id: int = None,
        forward_axis: str = "-Z",
        up_axis: str = "Y",
    ) -> "Mesh":
        """Load object from .obj file.

        :param obj_loc: Location of .obj file
        :param class_id: Class ID to assign to object
        :param forward_axis: Axis to use as forward axis
        :param up_axis: Axis to use as up axis


        Note: we use bpy.ops.wm.obj_import instead of bpy.ops.import_scene.obj because the latter
        causes issues with materials & vertex ordering.
        (Changing vertex ordering makes the use of keypoints difficult.)
        """
        for axis in (forward_axis, up_axis):
            assert axis in (
                "X",
                "Y",
                "Z",
                "-X",
                "-Y",
                "-Z",
            ), f"Axis `{axis}` not valid, must be one of X, Y, Z, -X, -Y, -Z"

        forward_axis = forward_axis.replace("-", "NEGATIVE_")  # e.g. -X -> NEGATIVE_X
        up_axis = up_axis.replace("-", "NEGATIVE_")

        assert os.path.isfile(obj_loc) and obj_loc.endswith(
            ".obj"
        ), f"File `{obj_loc}` not a valid .obj file"

        directory, fname = os.path.split(obj_loc)
        directory = os.path.abspath(directory)  # ensure absolute path for clean loading

        importer = GetNewObject(bpy.context.scene)
        with importer:
            bpy.ops.wm.obj_import(
                filepath=fname,
                directory=directory,
                filter_image=False,
                files=[{"name": fname}],
                forward_axis=forward_axis,
                up_axis=up_axis,
            )

        if class_id is None:
            class_id = default_ids["loaded_mesh"]

        obj = importer.imported_obj
        return cls(obj, class_id=class_id)

    @classmethod
    def from_glb(cls, glb_loc: str, class_id: int = None) -> "Mesh":
        """Load object from .glb file.

        :param glb_loc: Location of .glb file
        :param class_id: Class ID to assign to object
        """
        assert os.path.isfile(glb_loc) and glb_loc.endswith(
            (".glb", ".gtlf")
        ), f"File `{glb_loc}` not a valid .glb file"

        directory, fname = os.path.split(glb_loc)
        importer = GetNewObject(bpy.context.scene)
        with importer:
            bpy.ops.import_scene.gltf(filepath=glb_loc, files=[{"name": fname}])

        if class_id is None:
            class_id = default_ids["loaded_mesh"]

        return cls(importer.imported_obj, class_id=class_id)

    @classmethod
    def from_gltf(cls, gltf_loc: str, class_id: int = None) -> "Mesh":
        """Alias for :meth:`~blendersynth.blender.Mesh.from_glb`"""
        return cls.from_glb(gltf_loc, class_id=class_id)

    @classmethod
    def from_fbx(cls, fbx_loc: str, class_id: int = None) -> "Mesh":
        """Load object from .fbx file.

        :param fbx_loc: Location of .fbx file
        :param class_id: Class ID to assign to object"""
        assert os.path.isfile(fbx_loc) and fbx_loc.endswith(
            ".fbx"
        ), f"File `{fbx_loc}` not a valid .fbx file"

        directory, fname = os.path.split(fbx_loc)
        importer = GetNewObject(bpy.context.scene)
        with importer:
            bpy.ops.import_scene.fbx(filepath=fbx_loc, files=[{"name": fname}])

        if class_id is None:
            class_id = default_ids["loaded_mesh"]

        return cls(importer.imported_obj, class_id=class_id)

    @property
    def origin(self) -> Union[Vector, List[Vector]]:
        """
        Return origin of primary object.

        To get origins of all objects within the mesh, use :attr:`~blendersynth.blender.Mesh.all_origins`
        """
        return self.obj.location

    @origin.setter
    def origin(self, origin: Vector):
        """Set origin of primary object.

        :param origin: Origin to set

        To set origins of all objects within the mesh, use :attr:`~blendersynth.blender.Mesh.all_origins`
        """
        try:
            vec = handle_vec(origin)
        except ValueError:
            raise ValueError(
                f"Error with setting origin. Expects a 3 long Vector. Received: {origin}"
            )

        _set_object_origin(self._meshes[0], vec)

    @property
    def all_origins(self) -> List[Vector]:
        """Return list of origins of all objects within the mesh"""
        return [m.location for m in self._all_objects]

    @all_origins.setter
    def all_origins(self, origins: List[Vector]):
        """
        Set origins of all objects within the mesh.
        :param origins: List of origins to set
        """

        assert len(origins) == len(
            self._all_objects
        ), f"Expected {len(self._all_objects)} origins, got {len(origins)}"

        for i in range(len(self._all_objects)):
            try:
                vec = handle_vec(origins[i])
                _set_object_origin(self._all_objects[i], vec)
            except:
                raise ValueError(
                    f"Error with setting origins. Expects a list of {len(self._all_objects)} 3-long Vector. Received: {origins}"
                )

    def _get_all_vertices(self, ref_frame="WORLD") -> np.ndarray:
        """
        Get all vertices of object, taking into account deformations.
        :param ref_frame: LOCAL or WORLD
        :return: Nx3 array of vertices
        """

        depsgraph = bpy.context.evaluated_depsgraph_get()  # to account for deformations

        if ref_frame not in {"LOCAL", "WORLD"}:
            raise ValueError(
                f"Invalid ref_frame: {ref_frame}. Must be one of ['LOCAL', 'WORLD']"
            )

        verts = []

        for mesh in self._meshes:
            # use bmesh to get vertices - this accounts for deformations in depsgraph
            bm = bmesh.new()
            bm.from_object(mesh, depsgraph)
            bm.verts.ensure_lookup_table()
            mesh_verts = np.array([x.co for x in bm.verts])
            bm.free()

            if ref_frame == "WORLD":
                mesh_verts = np.dot(
                    mesh.matrix_world,
                    np.vstack((mesh_verts.T, np.ones(mesh_verts.shape[0]))),
                )

            verts.append(mesh_verts)

        verts = np.concatenate(verts, axis=1)
        verts /= verts[3]  # convert from homogeneous coordinates
        return verts[:3].T

    def get_raw_bounds(self) -> [Vector, Vector]:
        """Get the minimum and maximum bounds of all meshes in the object, under no deformations or transformations."""
        verts = np.array([v.co for mesh in self._meshes for v in mesh.data.vertices])
        bbox_min = Vector([*np.min(verts, axis=0)])
        bbox_max = Vector([*np.max(verts, axis=0)])
        return bbox_min, bbox_max

    @property
    def materials(self):
        return {m for mesh in self._meshes for m in mesh.data.materials}

    def assign_pass_index(self, index: int):
        """Assign pass index to object. This can be used when mask rendering.

        :param index: Pass index to assign"""
        for mesh in self._meshes:
            mesh.pass_index = index
        return index

    def assign_aov(self, aov: AOV):
        """Assign AOV to object. Applies to all materials.

        :param aov: AOV to assign"""
        if aov not in self.assigned_aovs:
            for material in self.materials:
                shader_node_tree = material.node_tree
                assert shader_node_tree is not None, "Material must have a node tree"
                aov.add_to_shader(shader_node_tree)

        self.assigned_aovs.append(aov)

    def assign_aovs(self, aovs: List[AOV]):
        """Assign multiple AOVs to object. Applies to all materials.

        :param aovs: AOVs to assign"""
        for aov in aovs:
            self.assign_aov(aov)

    def set_minimum_to(self, axis: str = "Z", pos: float = 0):
        """Set minimum of object to a given position in a given axis.

        :param axis: Axis to set minimum in
        :param pos: Position to set minimum to
        """
        min_pos = self._get_all_vertices("WORLD")[:, "XYZ".index(axis)].min()
        trans_vec = np.zeros(3)
        trans_vec["XYZ".index(axis)] = pos - min_pos
        self.translate(trans_vec)

    def clamp_in_axis(
        self, axis: str = "Z", mode: str = "min", value: float = 0
    ) -> np.ndarray:
        """Clamp object in a given axis to a given value - ensure that, in this axis,
        the object never goes below (mode='min') or above (mode='max') the given value.

        This can be used to ensure that an object never goes below the ground plane, for example.

        :param axis: Axis to clamp in
        :param mode: 'min' or 'max'
        :param value: Value to clamp to
        :return: Vector of translation applied to object
        """

        axis = axis.upper()
        assert axis in "XYZ", f"Invalid axis: {axis}"
        assert mode in {"min", "max"}, f"Invalid mode: {mode}"

        verts = self._get_all_vertices("WORLD")
        axis_idx = "XYZ".index(axis)

        translation = 0
        if mode == "min":
            translation = max(
                value - verts[:, axis_idx].min(), 0
            )  # can only be positive
        elif mode == "max":
            translation = min(
                value - verts[:, axis_idx].max(), 0
            )  # can only be negative

        trans_vec = np.zeros(3)
        trans_vec["XYZ".index(axis)] = translation
        self.translate(trans_vec)

        return trans_vec

    def delete(self, delete_materials: bool = True):
        """Clear mesh from scene & mesh data.

        :param delete_materials: Also delete object materials from scene"""
        mesh_names = [m.name for m in self._meshes]
        for mesh in self._meshes:
            bpy.data.objects.remove(mesh, do_unlink=True)

        # remove any non-mesh objects
        for obj in self._other_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Also remove its mesh data from bpy.data.meshes
        for mname in mesh_names:
            for m in bpy.data.meshes:
                if m.name == mname:
                    bpy.data.meshes.remove(m)
                    break

        self._meshes = []  # clear mesh list

        if delete_materials:
            for material in self.materials:
                bpy.data.materials.remove(material, do_unlink=True)

    def centroid(self, method: str = "median", seperate: bool = False) -> Vector:
        """
        Return the centroid of the mesh(es)

        :param method: See :attr:`~blendersynth.blender.mesh.Mesh.origin_to_centroid` for options.
        :param seperate: If True, will return a list of centroids for each object, rather than a single centroid.
        :return: Centroid of the mesh(es). If multiple meshes, will average the centroids.
        """

        if seperate:
            original_origins = deepcopy(self.all_origins)
            self.origin_to_centroid(method=method)
            centroids = deepcopy(self.all_origins)
            self.all_origins = original_origins
            return sum(centroids) / len(centroids)

        else:
            original_origin = deepcopy(self.origin)
            self.origin_to_centroid(method=method)
            centroid = deepcopy(self.origin)
            self.origin = original_origin
            return centroid

    def _set_origin_manual(self, origin: Vector, all_meshes=True):
        """Override to set origin manually. Should only be used by internal functions."""
        if all_meshes:
            for mesh in self._meshes:
                mesh.location = origin
        else:
            self._meshes[0].location = origin

    def origin_to_centroid(self, method: str = "bounds"):
        """Move object origin to centroid.

        Four methods available:

        * 'bounds' - move the origin to the center of the bounds of the mesh
        * 'median' - move the origin to the median point of the mesh
        * 'com_volume' - move to the centre of mass of the volume of the mesh
        * 'com_area' - Move to the centre of mass of the surface of the mesh

        :param method: Selected method to move origin to centroid
        """

        _valid_methods = ["bounds", "median", "com_volume", "com_area"]

        _type_lookup = dict(
            bounds="ORIGIN_GEOMETRY",
            median="ORIGIN_GEOMETRY",
            com_volume="ORIGIN_CENTER_OF_VOLUME",
            com_area="ORIGIN_CENTER_OF_MASS",
        )

        center = "BOUNDS" if method == "bounds" else "MEDIAN"

        with SelectObjects(self._meshes + self._other_objects):
            bpy.ops.object.origin_set(type=_type_lookup[method], center=center)

    def get_keypoints(
        self, idxs: list = None, position: Union[np.ndarray, List[Vector]] = None
    ) -> List[Vector]:
        """Return 3D keypoint positions in world coordinates, given either:

        :param idxs: list of indices or ndarray of keypoints to project (only valid for single-mesh objects)
        :param position: 3D position of keypoints to project - in LOCAL object coordinates

        :return: N list of Vectors of keypoints in world space, where N is the number of keypoints
        """

        assert (idxs is not None) ^ (
            position is not None
        ), "Must provide either idxs or position, but not both."

        if idxs is not None:
            assert (
                len(self._meshes) == 1
            ), "Can only project keypoints by index for single-mesh objects."
            kps3d = [
                self.matrix_world @ self._meshes[0].data.vertices[i].co for i in idxs
            ]

        elif position is not None:
            kps3d = [self.matrix_world @ p for p in position]

        return kps3d

    @property
    def name(self):
        return self._meshes[0].name

    def get_armature(self, armature_name: str = None) -> Armature:
        """Get armature.
        If no name given, return first armature found.

        :param armature_name: Name of armature to load."""

        armatures = [obj for obj in self._other_objects if obj.type == "ARMATURE"]

        if len(armatures) == 0:
            raise ValueError("No armatures found.")

        if armature_name is None:
            armature_name = armatures[0].name

        if armature_name in self._armatures:
            return self._armatures[armature_name]

        for arm in armatures:
            if arm.name == armature_name:
                bsyn_arm = Armature(arm)
                self._armatures[armature_name] = bsyn_arm
                return bsyn_arm

        raise KeyError(f"Armature `{armature_name}` not found.")

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, material: Material):
        self._material = material
        for mesh in self._meshes:
            mesh.data.materials.clear()
            mesh.data.materials.append(material.object)

    @property
    def shape_keys(self) -> bpy.types.Key:
        """Get the first shape keys object available"""
        for mesh in self._meshes:
            if mesh.data.shape_keys is not None:
                return mesh.data.shape_keys

        return None

    def get_shape_key(self, name: str) -> bpy.types.ShapeKey:
        """Get a given shape key object"""
        keys = self.shape_keys
        if keys is None:
            raise ValueError(f"Tried to get key '{name}' - no shape keys available.")

        elif name not in keys.key_blocks:
            raise ValueError(f"Tried to get key '{name}' - not found in shape keys.")

        return keys.key_blocks[name]

    def set_shape_key(self, name: str, value: float, frame: int = None):
        """Set shape key to a given value.

        :param name: Name of shape key
        :param value: Value to set shape key to
        :param frame: If not None, set keyframe at this frame
        """

        shape_key = self.get_shape_key(name)
        shape_key.value = value

        if frame is not None:
            shape_key.keyframe_insert(data_path="value", frame=frame)

    def set_shape_keys(self, data: dict, frame: int = None):
        """Set multiple shape keys at once.

        :param data: Dictionary of shape key names to values
        :param frame: If not None, set keyframe at this frame
        """
        for k, v in data.items():
            self.set_shape_key(k, v, frame=frame)

    def set_shape_key_data(self, name: str, data: np.ndarray):
        """Set shape key to a given value.

        :param name: Name of shape key
        :param data: Data to set shape key to
        """

        # self.get_shape_key(name).data.foreach_set("co", data.ravel())
        for i, coord in enumerate(data):
            self.get_shape_key(name).data[i].co = coord

    def make_shape_key(self, name: str, data: np.ndarray):
        """Create a new shape key, optionally with data.

        :param name: Name of shape key
        :param data: Data to set shape key to
        """

        if self.shape_keys is None:
            self.obj.shape_key_add(name="Basis")  # add basis shape key

        if name in self.shape_keys.key_blocks:
            raise ValueError(f"Shape key `{name}` already exists.")

        self.obj.shape_key_add(name=name)
        if data is not None:
            self.set_shape_key_data(name, data)

    @property
    def _all_objects(self):
        """List of all objects associated with this object."""
        return self._meshes + self._other_objects

    def add_child(self, obj: Union["Mesh", bpy.types.Object]):
        """Add child Mesh or Object to this object.
        This will make the child object move with this object.

        :param obj: Object to add as child
        """

        new_objects = []
        if isinstance(obj, Mesh):
            self._meshes += obj._meshes
            self._other_objects += obj._other_objects
            new_objects = obj._all_objects

        else:
            if obj.type == "MESH":
                self._meshes.append(obj)
            else:
                self._other_objects.append(obj)

            new_objects.append(obj)

        # add as children
        with SelectObjects(new_objects, active_object=self.obj):
            bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)

    def join(self, other_meshes: Union[List["Mesh"], List[bpy.types.Object]]):
        """
        Join other meshes into this mesh.
        :param other_meshes: List of either Mesh or blender Object types
        :return:
        """

        objects_to_join = []

        for other in other_meshes:
            if isinstance(other, Mesh):
                objects_to_join += other._all_objects

            elif isinstance(other, bpy.types.Object):
                objects_to_join += other

            else:
                raise ValueError(f"Cannot join object of type {type(other)} into Mesh.")

        with SelectObjects(objects_to_join, active_object=self.obj):
            bpy.ops.object.join()
