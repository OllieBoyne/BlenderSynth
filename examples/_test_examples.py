"""Validate that all examples in the examples directory run without error."""

import subprocess
import os

example_scripts = [f for f in os.listdir() if f.endswith('.py') and not f.startswith('_')]

for script in example_scripts:
	result = subprocess.run(['python', script], capture_output=True, text=True)

	# scan stdout for errors
	lines = result.stderr.split('\n') +  result.stdout.split('\n')
	for i, line in enumerate(lines):
		if 'Error' in line:
			print("\n".join([f"✖ Error in script {script}:", *lines[i:i+3], '']))
			break

	else:
		print(f"✓ Script {script} ran successfully")