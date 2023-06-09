import json
import os

def save_label(data, pth):
	os.makedirs(os.path.dirname(pth), exist_ok=True)
	with open(pth, 'w') as outfile:
		json.dump(data, outfile)