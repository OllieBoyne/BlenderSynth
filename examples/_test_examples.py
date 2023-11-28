"""Validate that all examples in the examples directory run without error."""

import subprocess
import os
import sys

example_scripts = [f for f in os.listdir() if f.endswith('.py') and not f.startswith('_')]
# place animation.py last because it takes a long time to run
example_scripts = sorted(example_scripts, key=lambda x: x == 'animation.py')

for script in example_scripts:
	print(f"Running script {script}")
	result = subprocess.run([sys.executable, script], capture_output=True, text=True)

	# scan stdout for errors
	lines = result.stderr.split('\n') + result.stdout.split('\n')
	for i, line in enumerate(lines):
		if 'Error' in line or 'Err' in line:
			print("\n".join([f"✖ Error in script {script}:", *lines[i:i+3], '']))
			break

	else:
		print(f"✓ Script {script} ran successfully")