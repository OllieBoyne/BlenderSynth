"""Generate the necessary .rst files for the docs, including editing index.rst"""

import os
from gen_api import tree as api_trees
from shutil import copyfile

# Path to the folders
tutorial_path = "tutorials"
example_path = "examples"
api_path = "api"

# The header for each section
tutorial_header = "Tutorials"
example_header = "Examples"
api_header = "API"

markdown_dir = os.path.join('docs', 'markdown')
static_img_dir = os.path.join('docs', '_static', 'images')
static_python_dir = os.path.join('docs', '_static', 'python')
python_dir = os.path.join('docs', 'python')

for dirs in [markdown_dir, static_img_dir, static_python_dir, python_dir]:
    os.makedirs(dirs, exist_ok=True)

def rel_to_docs(path):
    """Convert path /docs/.. to .."""
    return path.replace("docs" + os.sep, "")
def copy_markdown_file(src):
    """Copy over markdown file `src` to docs/markdown. For any references to images in the markdown file,
    copy to static/images and update the markdown file accordingly."""

    out_src = os.path.join(markdown_dir, os.path.basename(src))
    with open(src, "r") as f:
        lines = f.readlines()

    # Copy over images
    rel_dir = static_img_dir.replace("docs" + os.sep, "")
    for i, line in enumerate(lines):
        if line.startswith("!["):
            image_name = line.split("(")[1].split(")")[0]
            out_img_name = image_name.replace(os.sep, "%20")
            copyfile(os.path.join(os.path.dirname(src), image_name), os.path.join(static_img_dir, out_img_name))

            lines[i] = line.replace(image_name, os.path.join(rel_dir, out_img_name))

    # Write to file
    with open(out_src, "w") as f:
        f.writelines(lines)

    return rel_to_docs(out_src)

def copy_python_script(src):
    """Copy over python script `src` to <static_dir>/python.
    Create an rst in docs/python that links to the script properly."""

    static_python_src = os.path.join(static_python_dir, src.replace(os.sep, "%20"))
    copyfile(src, static_python_src)

    out_src = os.path.join("docs", "python", os.path.basename(src).replace(".py", ".rst"))
    os.makedirs(os.path.dirname(out_src), exist_ok=True)

    with open(out_src, "w") as f:
        top_line = f":code:`{src}`"
        f.write(top_line + "\n")
        f.write("=" * len(top_line) + "\n\n")
        f.write(f"""
.. literalinclude:: ../{rel_to_docs(static_python_src)}
   :language: python
""")
# You can view the `raw source code <../{rel_to_docs(static_python_src)}>`_.""")

    return rel_to_docs(out_src)


def get_files(path, extension):
    """Get all files with a certain extension in a directory."""
    return [os.path.splitext(f)[0] for f in os.listdir(path) if f.endswith(extension)]

def write_toctree(f, header, files):
    """Write a toctree to a file."""
    f.write(".. toctree::\n")
    f.write("   :maxdepth: 1\n")
    f.write("   :hidden:\n")
    f.write("   :caption: {0}\n\n".format(header))
    for file in files:
        f.write(f"   {file.replace('.rst', '')}\n")
    f.write("\n")

# Get the files
# tutorial_files = get_files(tutorial_path, ".md")

example_files = get_files(example_path, ".py")
example_rst_files = [copy_python_script(os.path.join(example_path, f"{file}.py")) for file in example_files]

api_files = [os.path.join(api_path, f"blendersynth.{tree}") for tree in api_trees]

# Write the index.rst
with open("docs/index.rst", "w") as f:
    # Include the README
    f.write(f".. mdinclude:: {copy_markdown_file('README.md')}\n\n")

    # Write the toctrees
    # write_toctree(f, tutorial_header, tutorial_files)
    write_toctree(f, example_header, example_rst_files)
    write_toctree(f, api_header, api_files)