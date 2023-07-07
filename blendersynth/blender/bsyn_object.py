"""Base class for all BlenderSynth objects."""

class BsynObject:
	"""Generic class for BlenderSynth objects."""
	_object = None # corresponding blender object

	@property
	def obj(self):
		return self._object

	@property
	def object(self):
		return self._object

	def keyframe_delete(self, *args, **kwargs):
		self._object.keyframe_delete(*args, **kwargs)

	def keyframe_insert(self, *args, **kwargs):
		self._object.keyframe_insert(*args, **kwargs)


def animatable_property(data_path:str, use_data_object:bool=False) -> callable:
	"""Decorator that wraps around a function to take a frame number and value, and set the property at that frame.

	example usage
	@animatable('location')
	def set_location(self, value):
		self._location = value

	If you want to set the property at the current frame, use the setter as normal:
	obj.set_location((1, 2, 3))

	To set the property at a specific frame, use the decorator:
	obj.set_location((1, 2, 3), frame=10)

	Which will call the set_location function, followed by
	self.object.keyframe_insert(data_path='location', frame=10)

	:param: data_path: the data path of the property to set
	:param: use_data_object: whether to use the data object or the object itself
	"""

	def wrapper(func):
		def subwrapper(self: BsynObject, value, frame=None):
			func(self, value)
			if frame is not None:
				object = self.object if not use_data_object else self.object.data
				object.keyframe_insert(data_path=data_path, frame=frame)

		return subwrapper

	return wrapper