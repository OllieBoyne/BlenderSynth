
from collections import namedtuple
from copy import deepcopy

_ann_types = ['bbox', 'keypoints', 'axes']

"""Per-camera annotation"""
Annotation = namedtuple('Ann', _ann_types, defaults=[None, None, None])


class AnnotationHandler:
	"""An object for storing annotations. Handles multiple types of annotation,
	as well as multiple camera views"""

	def __init__(self, data: dict):
		# internal store of camera_name: namedtuple of all data types
		self._data = data

	@classmethod
	def from_annotations(cls, data: dict, ann_type:str = 'bbox'):
		"""Create an Annotation Handler from a single type of annotation

		:param data: Dictionary of camera_name: annotation (e.g. bboxes)
		:param ann_type: Type of annotation (e.g. 'bbox')
		"""

		assert ann_type in _ann_types, f'Invalid annotation type: {ann_type}. Must be one of {_ann_types}'
		out_data = {}

		for cam_name, v in data.items():
			ann = Annotation()._replace(**{ann_type: v})
			out_data[cam_name] = ann

		return cls(out_data)

	def join(self, other: 'AnnotationHandler') -> 'AnnotationHandler':
		"""Combine two AnnotationHandlers, merging annotations wherever possible. Returns a new instance
		comprising the union of the two AnnotationHandlers.
		Where duplicates exist, other takes priority."""

		assert isinstance(other, AnnotationHandler), f'other must be an AnnotationHandler, not {type(other)}'

		_out_data = {}

		for cam_name, ann in self._data.items():
			out_ann = deepcopy(ann)
			if cam_name in other._data:
				other_ann = other.get_by_camera(cam_name)
				for ann_type in _ann_types:
					if getattr(other_ann, ann_type) is not None:
						out_ann = out_ann._replace(**{ann_type: getattr(other_ann, ann_type)})

			_out_data[cam_name] = out_ann

		for cam_name, ann in other._data.items():
			if cam_name not in _out_data:
				_out_data[cam_name] = deepcopy(ann)

		return AnnotationHandler(_out_data)

	def get_by_camera(self, camera_name) -> Annotation:
		"""Return annotation for a given camera (default to a NoneAnnotation if not found)"""
		return self._data.get(camera_name, Annotation())

	def __add__(self, other: 'AnnotationHandler'):
		return self.join(other)

