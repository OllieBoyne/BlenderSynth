"""Generate the necessary .rst files for the docs, including editing index.rst"""

import os

from gen_utils import copy_markdown_file
from gen_examples import generate_example_docs
from gen_utils import list_subfolders

# Path to the folders
tutorial_path = "tutorials"
example_path = "examples"
api_path = "api"

# The header for each section
tutorial_header = "Tutorials"
api_header = "API"

# preference for sorting, will defer to this where possible
examples_sort_order = ['quickstart', 'mesh_importing', 'texturing', 'output_data', 'dataset_creation', 'animation', 'capturing_pose',
                       'custom_aov', 'inverse_kinematics']

def get_sort_index(name, sort_order):
    """Get the index of the first 'match' in the sort order, or the length of the sort order if no match.
    a match is defined as the sort order being a substring of the name."""
    for n, i in enumerate(sort_order):
        if i in name:
            return n
    return len(sort_order)

def sort_by(name, sort_order):
    """Preferentially sort by the given sort order (by finding the first 'match' (see get_sort_index).
    Where not possible, sort alphabetically."""

    sorted_list = sorted(name, key=lambda x: (get_sort_index(x, sort_order), x))
    return sorted_list

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
api_files = [os.path.join(api_path, f"blendersynth.{f}") for f in sorted(list_subfolders('blendersynth'))]

# Write the index.rst
top_examples = generate_example_docs()
with open("docs/index.rst", "w") as f:
    # Include the README
    f.write(f".. mdinclude:: {copy_markdown_file('README.md')}\n\n")

    # Write the toctrees
    write_toctree(f, 'Examples', sort_by(top_examples, examples_sort_order))
    write_toctree(f, api_header, api_files)