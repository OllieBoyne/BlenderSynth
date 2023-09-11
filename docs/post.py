"""Postprocessing html docs for minor fixes"""

# fix 1 - remove BlenderSynth title from index.html
target = '<h1>BlenderSynth<a class="headerlink" href="#blendersynth" title="Permalink to this heading"></a></h1>'

with open('_build/index.html', 'r') as f:
	content = f.read()

if target in content:
	new_content = content.replace(target, '')

	with open('_build/index.html', 'w') as f:
		f.write(new_content)

else:
	raise ValueError(f"Postfix 1 failed - Could not find target {target} in index.html")


print("Run post checks ✔")