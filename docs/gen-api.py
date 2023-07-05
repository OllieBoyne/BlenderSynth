"""Generate API documentation."""

# EG
# blendersynth.file
# =========================


# blendersynth.file.dataset\_inputs
# ----------------------------------------
#
# .. automodule:: blendersynth.file.dataset_inputs
#    :members:
#    :undoc-members:
#    :show-inheritance:

import os

def list_directories(directory, ignore_dirs=['__pycache__']):
	return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f)) and f not in ignore_dirs]

def list_visible_python_scripts(directory):
	return [f for f in os.listdir(directory) if f.endswith('.py') and not f.startswith('__')]

directory = 'blendersynth'
out_dir = os.path.join('docs', 'api')
os.makedirs(out_dir, exist_ok=True)

for f in list_directories(directory):
	if '__' in f:
		continue

	outfile = os.path.join(out_dir, f'{directory}.{f}.rst')
	out_txt = f'{directory}.{f}\n=========================\n'

	for subf in list_visible_python_scripts(os.path.join(directory, f)) + list_directories(os.path.join(directory, f)):
		sub_name = subf.split('.')[0]  # remove .py if exists

		out_txt += f"""{directory}.{f}.{sub_name}
----------------------------------------

.. automodule:: {directory}.{f}.{sub_name}
   :imported-members:
   :members:
   :undoc-members:
   :show-inheritance:	

"""

	with open(outfile, 'w') as f:
		f.write(out_txt)