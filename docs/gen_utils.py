import os
from shutil import copyfile

markdown_dir = os.path.join('docs', 'markdown')
static_img_dir = os.path.join('docs', '_static', 'images')



def make_dirs(dirs):
	"""Make directories if they don't exist."""
	for d in dirs:
		os.makedirs(d, exist_ok=True)

def sep_conv(s, k = "%20"):
	"""Replace all separators with k."""
	return s.replace(os.sep, k)

def rel_to_docs(path):
	"""Convert path /docs/.. to .."""
	return os.path.relpath(path, "docs")

def rel_to_python(path):
	return os.path.relpath(path, os.path.join("docs", "python"))


def get_files(path, extension):
	"""Get all files with a certain extension in a directory."""
	return [os.path.splitext(f)[0] for f in os.listdir(path) if f.endswith(extension)]


def copy_markdown_file(src):
    """Copy over markdown file `src` to docs/markdown. For any references to images in the markdown file,
    copy to static/images and update the markdown file accordingly."""

    out_src = os.path.join(markdown_dir, sep_conv(src, '.'))
    with open(src, "r") as f:
        lines = f.readlines()

    # Copy over images
    rel_dir = static_img_dir.replace("docs" + os.sep, "")
    for i, line in enumerate(lines):
        if line.startswith("!["):
            image_name = line.split("(")[1].split(")")[0]
            out_img_name = sep_conv(image_name)
            copyfile(os.path.join(os.path.dirname(src), image_name), os.path.join(static_img_dir, out_img_name))

            lines[i] = line.replace(image_name, os.path.join(rel_dir, out_img_name))

    # Write to file
    with open(out_src, "w") as f:
        f.writelines(lines)

    return rel_to_docs(out_src)


make_dirs([markdown_dir, static_img_dir])