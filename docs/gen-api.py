"""Given a tree structure defining the API as we would like it, create the necessary .rst files, including editing index.rst"""

import os
import sys
import json

api_dir = os.path.join(os.path.dirname(__file__), 'api')
os.makedirs(api_dir, exist_ok=True)

tree = {
	'annotations': ['bbox', 'keypoints', 'utils'],
	'blender': ['aov', 'bsyn_object', 'camera', 'curve', 'light', 'mesh', 'render', 'utils', 'world'],
	'file': ['dataset_inputs', 'dataset_outputs', 'frames_to_video', 'tempfiles'],
	'run': ['blender_interface', 'blender_threading', 'run', 'run_this_script'],
	'utils': {'blender_setup': ['blender_locator', 'blender_python_path', 'check_blender_install'],
			  'node_arranger': []}
}



def manage_item(item, children):
	"""For each item, create .rst file.
	Children is either a list (no sub children), or a dict (has sub children).
	If has children, create .rst file for each child.
	For each child, add to .. toctree
	"""

	new_file = os.path.join(api_dir, f'{item}.rst')

	out_txt = f'{item}\n' + '=' * len(item) + '\n\n'

	if children:
		out_txt += f"""
.. toctree::
	:maxdepth: 1

"""
		for child in children:
			out_txt += f'	{item}.{child}\n'

			if isinstance(children, dict):
				manage_item(f'{item}.{child}', children[child])

			else:
				manage_item(f'{item}.{child}', [])

	else:
		out_txt += f"""
.. automodule:: {item}
	:members:
"""

	with open(new_file, 'w') as f:
		f.write(out_txt)


for item in tree:
	manage_item(f'blendersynth.{item}', tree[item])
