"""When constructing a dataset, the INPUTS object below will
return an iterable with read's in sys.argv's `--jobs` jsons."""

import sys
import json
import os

import logging

class INPUTS:
	"""This class is used to iterate over the JSONs passed in via `--jobs` in sys.argv."""
	jsons = None
	"""List of JSON files passed in via `--jobs` in sys.argv."""

	def __init__(self):
		self.jsons = sys.argv[sys.argv.index('--jobs') + 1].split(',')
		log_loc = sys.argv[sys.argv.index('--log') + 1]

		# Set up logging
		logging.basicConfig(filename=log_loc, level=logging.INFO, filemode='w',
							format='%(asctime)s - %(levelname)s - %(message)s')


	def __iter__(self):
		for n, j in enumerate(self.jsons):
			with open(j, 'r') as f:
				fname = os.path.splitext(os.path.split(j)[-1])[0]
				yield fname, json.load(f)

			# Once we get here, we've passed 'yield', so we know that JSON has been loaded & rendering has occured
			logging.info(f"RENDERED: {n:04d}")

	def __len__(self):
		return len(self.jsons)