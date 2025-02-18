"""Given a tree structure defining the API as we would like it, create the necessary .rst files, including editing index.rst"""

import os
import sys
import json
from gen_utils import list_scripts, list_subfolders

api_dir = os.path.join(os.path.dirname(__file__), 'api')
os.makedirs(api_dir, exist_ok=True)

src_dir = 'blendersynth'



def manage_item(src):
	"""
	If src is a directory, create a specialised .rst for this directory, and run recursively.
	If src is a .py script, create a .rst for this file.

	For each child, add to .. toctree
	"""

	fname = src.replace(os.path.sep, '.').replace('.py', '')

	new_file = os.path.join(api_dir, f'{fname}.rst')

	out_txt = f':code:`{fname}`\n' + '=' * (len(fname)+11) + '\n\n'

	if os.path.isdir(src):
		out_txt += f"""
.. toctree::
	:maxdepth: 1

"""
		for child in sorted(list_scripts(src) + list_subfolders(src)):
			child_fname = manage_item(os.path.join(src, child))
			out_txt += f'	{child_fname}\n'

	else:
		out_txt += f".. automodule:: {fname}\n\t:members:"

		# search python script for flags which affect doc building
		inherit_members = True
		special_members = ''
		with open(src, 'r') as f:
			for line in f.readlines():
				if '# no-inherited-members' in line:
					inherit_members = False

				if '# docs-special-members' in line:
					special_members = line.split(': ')[1]


		if inherit_members:
			out_txt += '\n\t:inherited-members:'

		if special_members:
			out_txt += f"\n\t:special-members: {special_members}\n"

	with open(new_file, 'w') as f:
		f.write(out_txt)

	return fname


manage_item(src_dir)
