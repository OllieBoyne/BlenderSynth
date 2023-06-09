"""Generate N labels with different eulers & locations"""
import os
import numpy as np
import json

json_dir = 'example_jsons'
N = 100

os.makedirs(json_dir, exist_ok=True)
for i in range(N):
	data = {
		'location': np.random.uniform(-0.3, 0.3, size=3).tolist(),
		'euler': np.random.uniform(-np.pi, np.pi, size=3).tolist()
	}

	with open(os.path.join(json_dir, f'{i:04d}.json'), 'w') as outfile:
		json.dump(data, outfile)