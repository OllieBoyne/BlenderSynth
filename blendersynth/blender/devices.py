"""Blender device management."""

import bpy
import warnings

def _isgpu(device):
	return device.type in {'CUDA', 'OPENCL', 'METAL'}

class DeviceList(list):
	@property
	def names(self):
		return [device.name for device in self]



class Devices():

	def __init__(self):
		self.device_list = DeviceList(bpy.context.preferences.addons['cycles'].preferences.devices)

	def set_device_usage(self, cpu: bool = True, cuda: bool = True,
							   opencl: bool = True, metal: bool = True):
		"""Set/unset all devices of certain types to enabled.

		:param cpu: Enable/disable CPU devices
		:param cuda: Enable/disable CUDA devices
		:param opencl: Enable/disable OpenCL devices
		:param metal: Enable/disable Metal devices
		"""

		for device in self.device_list:
			if device.type == 'CPU':
				device.use = cpu

			elif device.type == 'CUDA':
				device.use = cuda

			elif device.type == 'OPENCL':
				device.use = opencl

			elif device.type == 'METAL':
				device.use = metal

			else:
				warnings.warn(f'Unknown device type {device.type}')

	@property
	def available_gpus(self) -> DeviceList:
		"""Return list of all GPU devices."""
		return DeviceList(device for device in self.device_list if _isgpu(device))

	@property
	def enabled_gpus(self):
		"""Return list of available GPU devices."""
		return DeviceList(device for device in self.available_gpus if device.use)


	@property
	def device_names(self):
		"""Return a list of all device names."""
		return self.device_list.names

	@property
	def enabled_device_names(self):
		"""Return a list of named devices that are enabled."""
		return [device.name for device in self.device_list if device.use]

	def set_by_name(self, name:str, use=True):
		"""Set use/not use based on a device name.

		:param name: Device name
		:param use: Whether to use the device or not
		"""

		for device in self.device_list:
			if device.name == name:
				device.use = use
				return

		raise KeyError(f'No device named {name}. Available devices: {self.device_names}')