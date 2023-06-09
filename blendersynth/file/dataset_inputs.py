"""When constructing a dataset, the INPUTS object below will
return an iterable with read's in sys.argv's `--jobs` jsons."""
import sys
import json
import os

class INPUTS:
	def __init__(self):
		self.jsons = sys.argv[sys.argv.index('--jobs') + 1].split(',')

	def __iter__(self):
		for j in self.jsons:
			with open(j, 'r') as f:
				fname = os.path.splitext(os.path.split(j)[-1])[0]
				yield fname, json.load(f)

	def __len__(self):
		return len(self.jsons)