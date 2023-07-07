"""Generate the necessary .rst files for the docs, including editing index.rst"""

import os

from docs.gen_utils import copy_markdown_file
from gen_utils import make_dirs
from gen_api import tree as api_trees
from gen_examples import generate_example_docs

# Path to the folders
tutorial_path = "tutorials"
example_path = "examples"
api_path = "api"

# The header for each section
tutorial_header = "Tutorials"
api_header = "API"




def write_toctree(f, header, files):
    """Write a toctree to a file."""
    f.write(".. toctree::\n")
    f.write("   :maxdepth: 2\n")
    f.write("   :hidden:\n")
    f.write("   :caption: {0}\n\n".format(header))
    for file in files:
        f.write(f"   {file.replace('.rst', '')}\n")
    f.write("\n")

# Get the files
# tutorial_files = get_files(tutorial_path, ".md")


api_files = [os.path.join(api_path, f"blendersynth.{tree}") for tree in api_trees]

# Write the index.rst
top_examples = generate_example_docs()
with open("docs/index.rst", "w") as f:
    # Include the README
    f.write(f".. mdinclude:: {copy_markdown_file('README.md')}\n\n")

    # Write the toctrees
    # write_toctree(f, tutorial_header, tutorial_files)
    write_toctree(f, 'Examples', top_examples)
    write_toctree(f, api_header, api_files)