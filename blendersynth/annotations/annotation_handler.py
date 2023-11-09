from collections import namedtuple
from copy import deepcopy
from ..utils import types

# docs-special-members: __init__

ANN_TYPES = ["bbox", "keypoints", "axes"]
"""Valid annotation types"""


class Annotation:
    """A class for storing annotations for a single image."""

    def __init__(
        self,
        bbox: types.BboxAnnotation = None,
        keypoints: types.KeypointOrAxesAnnotation = None,
        axes: types.KeypointOrAxesAnnotation = None,
    ):
        """

        :param bbox: Bounding box tuple per instance
        :param keypoints: [N x 2] array per instance
        :param axes: [4 x 2] array per instance
        """
        self.bbox = bbox
        self.keypoints = keypoints
        self.axes = axes

    def __getitem__(self, item):
        return getattr(self, item)

    def _set(self, item, value) -> "Annotation":
        """In place set, returning self"""
        setattr(self, item, value)
        return self

    def set(self, item: str, value, inplace: bool = False) -> "Annotation":
        """Return a new Annotation, with item set to value.

        :param item: A key in :class:`ANN_TYPES`
        :param value: Value to set
        :param inplace: If True, set in place and return self
        """
        if inplace:
            return self._set(item, value)

        return self.copy()._set(item, value)

    def copy(self) -> "Annotation":
        """Return a deep copy of this Annotation instance"""
        return deepcopy(self)

    def union(self, other: "Annotation", priority="other") -> "Annotation":
        """Joins two annotations together, returning a new Annotation instance.

        :param other: Annotation to join with
        :param priority: Which annotation to take priority when merging
        """

        combined = Annotation()

        low_priority = "self" if priority == "other" else "other"

        for ann_type in ANN_TYPES:
            vals = {"self": self[ann_type], "other": other[ann_type]}

            if vals[priority] is not None:
                combined._set(ann_type, vals[priority])

            elif vals[low_priority] is not None:
                combined._set(ann_type, vals[low_priority])

        return combined

    def __add__(self, other: "Annotation"):
        return self.union(other)


class AnnotationHandler:
    """An object for storing and handling per-view :class:`Annotation` instances"""

    def __init__(self, data: dict):
        """
        :param data: Dictionary of camera_name: Annotation class
        """

        self._data = data

    @classmethod
    def from_annotations(
        cls, data: dict, ann_type: str = "bbox"
    ) -> "AnnotationHandler":
        """Create an Annotation Handler from a single type of annotation

        :param data: Dictionary of camera_name: annotation (e.g. bboxes)
        :param ann_type: Type of annotation (e.g. 'bbox')
        """

        assert (
            ann_type in ANN_TYPES
        ), f"Invalid annotation type: {ann_type}. Must be one of {ANN_TYPES}"
        out_data = {}

        for cam_name, v in data.items():
            ann = Annotation(**{ann_type: v})
            out_data[cam_name] = ann

        return cls(out_data)

    def union(
        self, other: "AnnotationHandler", priority: str = "other"
    ) -> "AnnotationHandler":
        """Combine two AnnotationHandlers, merging annotations wherever possible. Returns a new instance
        comprising the union of the two AnnotationHandlers.

        :param other: AnnotationHandler to merge with
        :param priority: Which AnnotationHandler to take priority when merging
        """

        assert isinstance(
            other, AnnotationHandler
        ), f"other must be an AnnotationHandler, not {type(other)}"

        out_data = {}
        camera_names = set(self._data.keys()).union(set(other._data.keys()))

        for camera_name in camera_names:
            self_ann, other_ann = self.get_annotation_by_camera(
                camera_name
            ), other.get_annotation_by_camera(camera_name)
            out_data[camera_name] = self_ann.union(other_ann, priority=priority)

        return AnnotationHandler(out_data)

    def get_annotation_by_camera(self, camera_name) -> Annotation:
        """Return annotation for a given camera (default to an empty :class:`Annotation` instance if not found)"""
        return self._data.get(camera_name, Annotation())

    def __add__(self, other: "AnnotationHandler"):
        return self.union(other)
