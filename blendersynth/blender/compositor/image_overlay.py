"""Overlay RGB image in compositor"""
from ..nodes import CompositorNodeGroup
import bpy
import cv2
import numpy as np
from ...file.tempfiles import create_temp_file
from typing import List
from ...utils import io


class AlphaImageOverlay(CompositorNodeGroup):
    """Overlay an image on top of the render, using the alpha channel of the image as a mask"""

    def __init__(self, name="AlphaImageOverlay", node_tree=None, scene=None):
        """Create a mix node which overlays an image on top of the input image."""

        super().__init__(name, node_tree)

        # Set default width and height
        self.width = 1000
        self.height = 1000
        if scene:
            self.width = scene.render.resolution_x
            self.height = scene.render.resolution_y

        # define I/O
        self.add_socket("NodeSocketColor", "Image", "INPUT")
        self.add_socket("NodeSocketColor", "Image", "OUTPUT")

        # create nodes
        self.overlay_img = self.group.nodes.new("CompositorNodeImage")
        self.mix_node = self.group.nodes.new("CompositorNodeMixRGB")
        self.sep_color_node = self.group.nodes.new("CompositorNodeSepRGBA")

        # link up internal nodes
        self.group.links.new(
            self.overlay_img.outputs["Image"], self.sep_color_node.inputs["Image"]
        )

        self.group.links.new(self.input_node.outputs["Image"], self.mix_node.inputs[1])
        self.group.links.new(self.overlay_img.outputs["Image"], self.mix_node.inputs[2])
        self.group.links.new(
            self.sep_color_node.outputs[3], self.mix_node.inputs["Fac"]
        )  # alpha

        self.group.links.new(
            self.mix_node.outputs["Image"], self.output_node.inputs["Image"]
        )

        self.create_img()

        self.tidy()

    def create_img(self):
        # create temp image to draw keypoints on, with 8 random alphanumeric characters
        # 8 random alphanum chars
        self.temp_img_loc = create_temp_file(".png")

        # initialize as white
        self.img = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        cv2.imwrite(self.temp_img_loc, self.img)

        # connect this image to the overlay node
        self.overlay_img.image = io.load_image(self.temp_img_loc)
        return self.temp_img_loc


class KeypointsOverlay(AlphaImageOverlay):
    """Overlay which draws keypoints on top of the render."""

    def __init__(
        self,
        name="KeypointsOverlay",
        node_tree=None,
        scene=None,
        camera=None,
        marker: str = "x",
        size: int = 5,
        color: tuple = (0, 0, 255),
        thickness: int = 2,
    ):
        """

        :param name:
        :param node_tree:
        :param scene:
        :param camera:
        :param marker: Marker type, either [c/circle], [s/square], [t/triangle] or [x]. Default 'x'
        :param size: Size of marker. Default 5
        :param color: Color of marker, RGB or RGBA, default (0, 0, 255) (red)
        :param thickness: Thickness of marker. Default 2
        """
        super().__init__(name, node_tree)

        self.marker = marker
        self.size = size
        self.color = color
        self.thickness = thickness

    def update(
        self,
        keypoints: np.ndarray,
        scene: bpy.types.Scene = None,
        camera: bpy.types.Camera = None,
    ):
        """Given [N x 3] keypoints, draw them onto a new temp image.

        :param keypoints: N x 3 keypoints
        :param scene: Scene to draw from
        :param camera: Camera

        """

        self.width = scene.render.resolution_x
        self.height = scene.render.resolution_y

        # reset image to black, with alpha = 0
        self.img = np.zeros((self.height, self.width, 4), dtype=np.uint8)

        color = self.color
        if len(color) == 3:
            color = (*color, 255)  # add alpha

        # draw keypoints on image
        size = self.size
        for kp in keypoints:
            if self.marker in ["c", "circle"]:
                cv2.circle(
                    self.img, (int(kp[0]), int(kp[1])), size, color, self.thickness
                )
            elif self.marker in ["s", "square"]:
                cv2.rectangle(
                    self.img,
                    (int(kp[0]) - size, int(kp[1]) - size),
                    (int(kp[0]) + size, int(kp[1]) + size),
                    color,
                    self.thickness,
                )
            elif self.marker in ["t", "triangle"]:
                points = np.array(
                    [
                        [kp[0], kp[1] - size],
                        [kp[0] - size, kp[1] + size],
                        [kp[0] + size, kp[1] + size],
                    ],
                    dtype=np.int32,
                )
                cv2.polylines(
                    self.img,
                    [points],
                    isClosed=True,
                    color=color,
                    thickness=self.thickness,
                )
                cv2.fillPoly(self.img, [points], color=color)
            elif self.marker == "x":
                cv2.line(
                    self.img,
                    (int(kp[0]) - size, int(kp[1]) - size),
                    (int(kp[0]) + size, int(kp[1]) + size),
                    color,
                    self.thickness,
                )
                cv2.line(
                    self.img,
                    (int(kp[0]) + size, int(kp[1]) - size),
                    (int(kp[0]) - size, int(kp[1]) + size),
                    color,
                    self.thickness,
                )
            else:
                raise ValueError("Invalid marker: {}".format(self.marker))

        self.save_image(self.temp_img_loc, self.img)


class BoundingBoxOverlay(AlphaImageOverlay):
    """Overlay which draws bounding boxes on top of the render."""

    def __init__(
        self,
        name="BoundingBoxOverlay",
        node_tree=None,
        scene=None,
        camera=None,
        col: tuple = (0, 0, 255, 255),
        thickness: int = 2,
    ):
        super().__init__(name, node_tree)
        self.col = col
        self.thickness = int(thickness)  # cv2 requires int

    def update(self, bboxes, scene=None, camera=None):
        """Given [N x 4] bounding boxes, draw them onto a new temp image."""

        self.width = scene.render.resolution_x
        self.height = scene.render.resolution_y

        # reset image to black, with alpha = 0
        self.img = np.zeros((self.height, self.width, 4), dtype=np.uint8)

        col = self.col
        if len(col) == 3:
            col = (col[0], col[1], col[2], 255)

        # draw bounding boxes on image
        for bbox in bboxes:
            cv2.rectangle(
                self.img,
                (int(bbox[0]), int(bbox[1])),
                (int(bbox[2]), int(bbox[3])),
                col,
                self.thickness,
            )

        self.save_image(self.temp_img_loc, self.img)


class AxesOverlay(AlphaImageOverlay):
    """Overlay which draws axes on top of an existing render"""

    def __init__(
        self,
        name="BoundingBoxOverlay",
        node_tree=None,
        scene=None,
        camera=None,
        size: int = 1,
        thickness: int = 2,
    ):
        super().__init__(name, node_tree)

        self.size = size
        self.thickness = thickness

    def update(
        self,
        points: List[np.ndarray],
        scene: bpy.types.Scene = None,
        camera: bpy.types.Camera = None,
    ):
        """Plot axes onto the image.

        :param points: list of N x 4 2D points of centre + XYZ unit axes
        :param scene: Scene
        :param camera: Camera"""

        self.width = scene.render.resolution_x
        self.height = scene.render.resolution_y
        self.img = np.zeros((self.height, self.width, 4), dtype=np.uint8)

        for P in points:
            centre = P[0].astype(int)
            for i, point in enumerate(P[1:]):
                offset = point - centre
                point2 = centre + offset * self.size
                x, y = map(int, centre)
                x2, y2 = map(int, point2)
                # note BGR color order
                # and -y because image y-axis is flipped
                self.img = cv2.line(
                    self.img,
                    (x, y),
                    (x2, y2),
                    (255 * (i == 2), 255 * (i == 1), 255 * (i == 0), 255),
                    self.thickness,
                )

        self.save_image(self.temp_img_loc, self.img)
