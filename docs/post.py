"""Postprocessing html docs for minor fixes"""
import re

regexSearch = re.compile(r'<h1>BlenderSynth<.*></h1>')

with open('_build/index.html', 'r') as f:
	content = f.read()

if re.search(regexSearch, content):
	new_content = re.sub(regexSearch, '', content)

	with open('_build/index.html', 'w') as f:
		f.write(new_content)

else:
	print(f"Postfix 1 failed - Could not find target BlenderSynth title in index.html")


print("Run post checks ✔")