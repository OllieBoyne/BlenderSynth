import os
from shutil import copyfile
from gen_utils import rel_to_docs, make_dirs, sep_conv, copy_markdown_file


static_python_dir = os.path.join('docs', '_static', 'python')
python_dir = os.path.join('docs', 'python')

examples_dir = 'examples'

make_dirs([static_python_dir, python_dir])

always_caps_words = ['AOV'] # always capitalize these words

blacklist = ['README.md']

def is_py_script(src):
	file = os.path.basename(src)
	return file.endswith(".py") and not file.startswith('_')

def is_script_directory(src):
	contains_scripts = any(is_py_script(file) for file in os.listdir(src))
	subfolders_contain_scripts = any(is_script_directory(os.path.join(src, file)) for file in os.listdir(src) if os.path.isdir(os.path.join(src, file)))
	return contains_scripts or subfolders_contain_scripts

def format_script_name(src):
	"""We want to format the name of scripts as viewed in the headers/sidebars in the following ways:

	- Just get the name of the path/directory
	- Sentence case
	- Replace underscores with spaces
	- Remove extension
	- Capitalize any words in always_caps_words
	"""

	formatted = os.path.splitext(os.path.basename(src))[0].replace("_", " ").capitalize()
	formatted = " ".join([s, s.upper()][s.upper() in always_caps_words] for s in formatted.split())
	return formatted

def copy_python_script(src):
	"""
	a) create rst in docs/python that links to the script properly.
	b) Copy over python script `src` to <static_dir>/python.
	If src is a directory, create a specialised .rst for this directory, and run recursively.

	returns the path to the rst file."""

	if os.path.isdir(src) and is_script_directory(src):

		out_dir = os.path.join("docs", "python", os.path.relpath(src, examples_dir))
		os.makedirs(out_dir, exist_ok=True)

		sub_locs = []
		for f in os.listdir(src):
			subl = copy_python_script(os.path.join(src, f))
			if subl is not None:
				sub_locs.append(os.path.relpath(subl, os.path.relpath(out_dir, "docs")))  # get relative path to out_dir

		out_src = os.path.join(out_dir, "index.rst")

		with open(out_src, "w") as f:
			top_line = format_script_name(src)
			f.write(top_line + "\n")
			f.write("=" * len(top_line) + "\n\n")

			for s in sub_locs:
				if s.lower().endswith('readme.md'):
					f.write(f".. mdinclude:: {s}\n\n")

			f.write(".. toctree::\n")
			f.write("   :maxdepth: 1\n\n")

			for s in sub_locs:
				if s.endswith(".rst"):
					f.write(f"   {os.path.splitext(s)[0]}\n")

			f.write("\n")

		return rel_to_docs(out_src)


	elif is_py_script(src):
		static_python_src = os.path.join(static_python_dir, sep_conv(src, '.'))
		copyfile(src, static_python_src)

		out_src = os.path.join("docs", "python", os.path.relpath(src, examples_dir).replace(".py", ".rst"))
		os.makedirs(os.path.dirname(out_src), exist_ok=True)

		with open(out_src, "w") as f:
			top_line = format_script_name(src)
			f.write(top_line + "\n")
			f.write("=" * len(top_line) + "\n\n")

			# if an .md file exists with the same name, include it
			markdown_loc = src.replace(".py", ".md")
			if not os.path.exists(markdown_loc): markdown_loc = markdown_loc.replace(".md", ".MD")  # may be capitalized
			if os.path.exists(markdown_loc):
				static_markdown = copy_markdown_file(markdown_loc, rel_dir=os.path.dirname(out_src))
				f.write(f".. mdinclude:: {os.path.relpath(static_markdown, os.path.relpath(os.path.dirname(out_src), 'docs'))}\n\n")

			f.write(f"""
.. literalinclude:: {os.path.relpath(static_python_src, os.path.dirname(out_src))}
   :language: python
	""")

	elif src.lower().endswith('readme.md'):
		return copy_markdown_file(src, rel_dir=os.path.dirname(src))

	else:
		return None

	return rel_to_docs(out_src)

def python_toctree(f, files):
	"""Write a toctree to a file."""
	f.write(".. toctree::\n")
	f.write("   :maxdepth: 3\n")
	f.write("   :hidden:\n")
	f.write("   :caption: Examples\n\n")
	for file in files:
		f.write(f"   {file.replace('.rst', '')}\n")
	f.write("\n")

def generate_example_docs():
	"""Generate documentation for examples."""
	items = []
	for f in os.listdir("examples"):
		if f in blacklist:
			continue

		i = copy_python_script(os.path.join("examples", f))
		if i is not None:
			items.append(i)

	return items