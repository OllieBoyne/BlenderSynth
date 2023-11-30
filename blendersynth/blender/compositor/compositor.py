import bpy
from ..utils import get_node_by_name
import os
import shutil
from ..render import render, render_depth
from ..nodes import CompositorNodeGroup
from ..aov import AOV
from .mask_overlay import MaskOverlay
from .visuals import DepthVis
from .image_overlay import (
    KeypointsOverlay,
    BoundingBoxOverlay,
    AlphaImageOverlay,
    AxesOverlay,
)
from ...annotations import Annotation, AnnotationHandler
from ..nodes import tidy_tree
from ..world import world
from ..camera import Camera
from ...utils import version

from typing import Union, List

# Mapping of file formats to extensions
format_to_extension = {
    "BMP": ".bmp",
    "IRIS": ".rgb",
    "PNG": ".png",
    "JPEG": ".jpg",
    "JPEG2000": ".jp2",
    "TARGA": ".tga",
    "TARGA_RAW": ".tga",
    "CINEON": ".cin",
    "DPX": ".dpx",
    "OPEN_EXR_MULTILAYER": ".exr",
    "OPEN_EXR": ".exr",
    "HDR": ".hdr",
    "TIFF": ".tif",
    # Add more formats if needed
}

AVAILABLE_FORMATS = [
    "BMP",
    "IRIS",
    "PNG",
    "JPEG",
    "JPEG2000",
    "TARGA",
    "TARGA_RAW",
    "CINEON",
    "DPX",
    "OPEN_EXR_MULTILAYER",
    "OPEN_EXR",
    "HDR",
    "TIFF",
]
"""List of available output file formats"""

# docs-special-members: __init__

def _default_color_space():
    """Get default color space for Blender version"""
    if version.is_version_plus(4):
        return "AgX Base sRGB"
    else:
        return "Filmic sRGB"

def _get_badfname(fname, N=100):
    """Search for filename in the format
    <main_fname><i:04d>.<ext>
    where i is the frame number. if no file found for i < N, raise error.
    otherwise, return found file
    """
    f, ext = os.path.splitext(fname)
    for i in range(N):
        fname = f + f"{i:04d}" + ext
        if os.path.isfile(fname):
            return fname

    raise FileNotFoundError(f"File {fname} not found")


def _all_anim_frames(fname, N=1000):
    """Search for filename in the format
    <main_fname><i:04d>.<ext>
    where i is the frame number. if no file found for i < N, raise error.
    otherwise, return found file
    """
    f, ext = os.path.splitext(fname)
    for i in range(N):
        fname = f + f"{i:04d}" + ext
        if os.path.isfile(fname):
            yield fname
        else:
            break


def remove_ext(fname):
    return os.path.splitext(fname)[0]  # remove extension if given


class Compositor:
    """Compositor output - for handling file outputs, and managing Compositor node tree"""

    def __init__(
        self,
        view_layer="ViewLayer",
        background_color: tuple = None,
        rgb_color_space: str = None,
    ):
        """
        :param view_layer: Name of View Layer to render
        :param background_color: If given, RGB[A] tuple in range [0-1], will overwrite World background with solid color (while retaining lighting effects).
        :param rgb_color_space: Color transform for RGB only. Defaults to `AgX Base sRGB` for Blender 4+, and `Filmic sRGB` for older versions.
        """

        if rgb_color_space is None:
            rgb_color_space = _default_color_space()

        # Create compositor node tree
        bpy.context.scene.use_nodes = True
        self.node_tree = bpy.context.scene.node_tree

        self.view_layer = view_layer  #

        self.file_output_nodes = {}  # Mapping of output name to FileOutputNode
        self.mask_nodes = {}  # Mapping of mask pass index to CompositorNodeGroup
        self.overlays = {}
        self.aovs = []  # List of AOVs (used to update before rendering)

        # We set view transform to 'Raw' to avoid any gamma correction to all non-Image layers
        bpy.context.scene.view_settings.view_transform = "Raw"

        # Socket to be used as RGB input for anything. Defined separately in case of applying overlays (e.g. background color)
        self._rgb_socket = get_node_by_name(self.node_tree, "Render Layers").outputs[
            "Image"
        ]
        self._set_rgb_color_space(rgb_color_space)
        if background_color is not None:
            self._set_background_color(background_color)

    def _tidy_tree(self):
        """Tidy up node tree"""
        tidy_tree(self.node_tree)

    @property
    def render_layers_node(self):
        return get_node_by_name(self.node_tree, "Render Layers")

    def _get_render_layer_output(self, key: str):
        """Get output socket from Render Layers node"""
        if key == "Image":  # special case
            return self._rgb_socket
        else:
            return self.render_layers_node.outputs[key]

    def get_mask(
        self, index, input_rgb: Union[str, CompositorNodeGroup], anti_aliasing=False
    ) -> CompositorNodeGroup:
        """Get mask node from pass index. If not found, create new mask node"""
        bpy.context.scene.view_layers[
            self.view_layer
        ].use_pass_object_index = True  # Make sure object index is enabled

        if index not in self.mask_nodes:
            if isinstance(input_rgb, str):
                ip_node = self._get_render_layer_output(input_rgb)

            elif isinstance(input_rgb, CompositorNodeGroup):
                ip_node = input_rgb.outputs["Image"]

            else:
                raise TypeError(
                    f"input_rgb must be str or CompositorNodeGroup, got {type(input_rgb)}"
                )

            dtype = (
                "Float" if isinstance(ip_node, bpy.types.NodeSocketFloat) else "Color"
            )

            cng = MaskOverlay(
                f"Mask - ID: {index} - Input {input_rgb}",
                self.node_tree,
                index=index,
                dtype=dtype,
                use_antialiasing=anti_aliasing,
            )

            self.node_tree.links.new(ip_node, cng.input("Image"))
            self.node_tree.links.new(
                self._get_render_layer_output("IndexOB"), cng.input("IndexOB")
            )
            self.mask_nodes[index] = cng

        self._tidy_tree()
        return self.mask_nodes[index]

    def get_bounding_box_visual(
        self, col=(0.0, 0.0, 255.0, 255.0), thickness: int = 5
    ) -> BoundingBoxOverlay:
        """
        Return a bounding box visual overlay.

        :param col: (3,) or (N, 3) Color(s) of bounding box(es) [in BGR]
        :param thickness: (,) or (N,) Thickness(es) of bounding box(es)
        """

        cng = BoundingBoxOverlay(
            f"Bounding Box Visual", self.node_tree, col=col, thickness=thickness
        )
        self.node_tree.links.new(
            self._get_render_layer_output("Image"), cng.input("Image")
        )

        if "bbox" in self.overlays:
            raise ValueError(
                "Only allowed one BBox overlay (it can contain multiple objects)."
            )

        self.overlays["bbox"] = cng

        self._tidy_tree()
        return cng

    def get_keypoints_visual(
        self,
        marker: str = "x",
        color: tuple = (0, 0, 255),
        size: int = 5,
        thickness: int = 2,
    ) -> KeypointsOverlay:
        """
        Return a keypoints visual overlay.

        :param marker: Marker type, either [c/circle], [s/square], [t/triangle] or [x]. Default 'x'
        :param size: Size of marker. Default 5
        :param color: Color of marker, RGB or RGBA, default (0, 0, 255) (red)
        :param thickness: Thickness of marker. Default 2
        """

        cng = KeypointsOverlay(
            f"Keypoints Visual",
            self.node_tree,
            marker=marker,
            color=color,
            size=size,
            thickness=thickness,
        )
        self.node_tree.links.new(
            self._get_render_layer_output("Image"), cng.input("Image")
        )

        if "keypoints" in self.overlays:
            raise ValueError("Only allowed one Keypoints overlay.")

        self.overlays["keypoints"] = cng

        self._tidy_tree()
        return cng

    def get_axes_visual(self, size: int = 1, thickness: int = 2) -> AxesOverlay:
        """
        Return an axes visual overlay.

        :param size: Size of axes. Default 100
        :param thickness: Thickness of axes. Default 2
        """

        cng = AxesOverlay(
            f"Axes Visual", self.node_tree, size=size, thickness=thickness
        )
        self.node_tree.links.new(
            self._get_render_layer_output("Image"), cng.input("Image")
        )

        if "axes" in self.overlays:
            raise ValueError("Only allowed one Axes overlay.")

        self.overlays["axes"] = cng
        self._tidy_tree()
        return cng

    def stack_visuals(self, *visuals: AlphaImageOverlay) -> AlphaImageOverlay:
        """Given a series of image overlays, stack them and return to be used as a single output node.

        :param *visuals: Stack of overlays to add."""

        if len(visuals) < 2:
            raise ValueError("Requires at least 2 visuals to stack")

        # No need to store these overlays separately in self.overlays, but need to check they're all present
        for overlay in visuals:
            if overlay not in self.overlays.values():
                raise ValueError(
                    f"Visual {overlay} not found in Compositor. Make sure it was obtained via the Compositor."
                )

        # Stack the output of the previous to the input of the next
        for va, vb in zip(visuals, visuals[1:]):
            self.node_tree.links.new(va.output("Image"), vb.input("Image"))

        return visuals[-1]

    def get_depth_visual(
        self, max_depth=1, col: tuple = (255, 255, 255)
    ) -> CompositorNodeGroup:
        """Get depth visual, which normalizes depth values so max_depth = col,
        and any values below that are depth/max_depth * col.

        :param max_depth: Maximum depth value to normalize to
        :param col: Color of maximum depth value. 0-255 RGB or RGBA."""

        if "Depth" not in self.render_layers_node.outputs:
            render_depth()

        # convert col to 0-1, RGBA
        col = ([i / 255 for i in col] + [1])[:4]

        cng = DepthVis(self.node_tree, max_depth=max_depth, col=col)
        self.node_tree.links.new(
            self._get_render_layer_output("Depth"), cng.input("Depth")
        )

        self._tidy_tree()
        return cng

    def define_output(
        self,
        input_data: Union[str, CompositorNodeGroup, AOV],
        directory: str = ".",
        file_name: str = None,
        file_format: str = "PNG",
        color_mode: str = "RGBA",
        jpeg_quality: int = 90,
        png_compression: int = 15,
        color_depth: str = "8",
        EXR_color_depth: str = "32",
        name: str = None,
    ) -> str:
        """Add a connection between a valid render output, and a file output node.

        This should only be called once per output (NOT inside a loop).
        Inside the loop, only call :attr:`~update_filename`, :attr:`update_all_filenames` :attr:`~update_directory`

        All outputs will be defined in raw color space (no color correction), except for the RGB output,
        and any overlays on this output (e.g. Bounding Box Visualization)

        :param input_data: If :class:`str`,  will get the input_data from that key in the render_layers_node. If :class:`~CompositorNodeGroup`, use that node as input. If :class:`AOV`, use that AOV as input (storing AOV).
        :param directory: Directory to save output to
        :param file_name: Name of file to save output to. If None, will use `name` (or `input_data` if `name` is None)
        :param file_format: File format to save output as. Must be in :class:`AVAILABLE_FORMATS`
        :param color_mode: Color mode to save output as.
        :param jpeg_quality: Quality of JPEG output.
        :param png_compression: Compression of PNG output.
        :param color_depth: Color depth of output.
        :param EXR_color_depth: Color depth of EXR output.
        :param name: Name of output. If not given, will take the str representation of input_data

        :returns: Name of output, which can be used to update filename or directory

        """

        if isinstance(input_data, AOV):
            self.aovs.append(input_data)
            input_data = (
                input_data.name
            )  # name is sufficient to pull from render_layers_node

        assert (
            file_format in format_to_extension
        ), f"File format `{file_format}` not supported. Options are: {list(format_to_extension.keys())}"

        if name is None:
            name = str(input_data)

        node_name = f"File Output {name}"

        # check node doesn't exist
        if name in self.file_output_nodes:
            raise ValueError(
                f"File output `{name}` already exists. Only call define_output once per output type."
            )

        if file_name is None:  # if fname is not given, use input_name
            file_name = name

        file_name = remove_ext(file_name)
        directory = os.path.abspath(directory)  # make sure directory is absolute
        os.makedirs(directory, exist_ok=True)

        # Create new 'File Output' node in compositor
        node = self.node_tree.nodes.new("CompositorNodeOutputFile")
        node.name = node_name

        if isinstance(input_data, str):
            self.node_tree.links.new(
                self._get_render_layer_output(input_data), node.inputs["Image"]
            )

        elif isinstance(input_data, CompositorNodeGroup):  # add overlay in between
            self.node_tree.links.new(input_data.outputs[0], node.inputs["Image"])

        else:
            raise NotImplementedError(
                f"input_data must be either str or CompositorNodeGroup, got {type(input_data)}"
            )

        # Set file output node properties
        node.label = node_name
        node.base_path = directory
        node.file_slots[0].path = file_name

        # File format kwargs
        node.format.file_format = file_format
        node.format.color_mode = color_mode
        node.format.quality = jpeg_quality
        node.format.compression = png_compression
        node.format.color_depth = (
            color_depth if file_format != "OPEN_EXR" else EXR_color_depth
        )

        self.file_output_nodes[name] = node

        self._tidy_tree()
        return name

    def update_filename(self, key: str, fname: str):
        """Reassign the filename (not directory) for a given file output node.

        :param key: key of output, as given in `define_output`
        :param fname: new filename, without extension"""
        fname = remove_ext(fname)
        node = self.file_output_nodes[str(key)]
        node.file_slots[0].path = fname

    def update_all_filenames(self, fname: str):
        """Reassign all filenames (not directories) for all file output nodes.

        :param fname: new filename, without extension"""
        fname = remove_ext(fname)
        for node in self.file_output_nodes.values():
            node.file_slots[0].path = fname

    def update_directory(self, key: str, directory: str):
        """Reassign the directory for a given file output node

        :param key: key of output, as given in `define_output`
        :param directory: new directory
        """
        node = self.file_output_nodes[str(key)]
        node.base_path = directory

    def _fix_namings_static(self, prefix=None):
        """After rendering a static scene,
        File Output node has property that frame number gets added to filename.
        Fix that here"""

        prefix = "" if prefix is None else prefix + "_"

        for node in self.file_output_nodes.values():
            # get expected file name and extension
            ext = format_to_extension[node.format.file_format]
            bad_file_name = _get_badfname(
                os.path.join(node.base_path, node.file_slots[0].path + ext)
            )
            target_file_name = os.path.join(
                node.base_path, prefix + node.file_slots[0].path + ext
            )
            shutil.move(bad_file_name, target_file_name)

    def _fix_namings_animation(self, prefix=None):
        """After rendering an animation, find all the files that have been rendered,
        and prepend prefix to them"""
        if prefix is None:
            return

        for node in self.file_output_nodes.values():
            # get expected file name and extension
            ext = format_to_extension[node.format.file_format]
            for fname in _all_anim_frames(
                os.path.join(node.base_path, node.file_slots[0].path + ext)
            ):
                target_file_name = os.path.join(
                    node.base_path, prefix + "_" + os.path.basename(fname)
                )
                shutil.move(fname, target_file_name)

    def _update_aovs(self):
        """Update any AOVs that are connected to the render layers node"""
        for aov in self.aovs:
            aov.update()

    def render(
        self,
        camera: Union[Camera, List[Camera]] = None,
        scene: bpy.types.Scene = None,
        annotations: AnnotationHandler = None,
        animation: bool = False,
        frame_start: int = 0,
        frame_end: int = 250,
    ):
        """Render the scene.

        :param camera: Camera(s) to render from. If None, will use `scene.camera`. If multiple, will render each camera separately, appending the camera's names as the output file names.
        :param scene: Scene to render. If None, will use `bpy.context.scene`.
        :param annotations: Object containing annotation information for each camera view to be used for overlays
        :param animation: If True, will render an animation, using `frame_start` and `frame_end` as the start and end frames.
        :param frame_start: Start frame for animation.
        :param frame_end: End frame for animation.
        """

        if scene is None:
            scene = bpy.context.scene

        _original_active_camera = bpy.context.scene.camera
        if camera is None:
            camera = Camera()

        if animation:
            scene.frame_start = frame_start
            scene.frame_end = frame_end

        multi_camera = isinstance(camera, list)
        if not multi_camera:
            camera = [camera]

        for cam in camera:
            if annotations is not None:
                annotation = annotations.get_annotation_by_camera(cam.name)

                # apply overlays PER CAMERA
                for oname, overlay in self.overlays.items():
                    overlay.update(
                        getattr(annotation, oname), camera=cam, scene=scene
                    )  # multi kwargs

            self._update_aovs()

            scene.camera = cam.obj
            render(animation=animation)

            if animation:
                self._fix_namings_animation(prefix=cam.name if multi_camera else None)

            else:
                self._fix_namings_static(prefix=cam.name if multi_camera else None)

        # reset active camera
        scene.camera = _original_active_camera

    def _set_rgb_color_space(self, color_space: str = "Filmic sRGB"):
        """Color spaces are all handled manually within compositor (so that we keep
        AOVs in raw space). So set the color space for RGB socket here."""

        color_space_node = self.node_tree.nodes.new("CompositorNodeConvertColorSpace")
        color_space_node.from_color_space = "Non-Color"
        color_space_node.to_color_space = color_space

        self.node_tree.links.new(self._rgb_socket, color_space_node.inputs[0])
        self._rgb_socket = color_space_node.outputs[0]

    def _set_background_color(self, color: tuple = (0, 0, 0)):
        """Set a solid background color, instead of transparent.
        Will remove the visuals of existing world background (but not the lighting effects).

        :param color: RGBA color, in range [0, 1]
        """

        world.set_transparent()

        rgba = color
        if len(rgba) == 3:
            rgba = (*rgba, 1)

        rgb_node = self.node_tree.nodes.new("CompositorNodeRGB")
        rgb_node.outputs[0].default_value = rgba

        mix_node = self.node_tree.nodes.new("CompositorNodeMixRGB")

        self.node_tree.links.new(self._rgb_socket, mix_node.inputs[2])
        self.node_tree.links.new(rgb_node.outputs[0], mix_node.inputs[1])

        self.node_tree.links.new(
            self._get_render_layer_output("Alpha"), mix_node.inputs["Fac"]
        )
        self._rgb_socket = mix_node.outputs["Image"]
