# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys

sys.path.insert(0, '../')

project = 'BlenderSynth'
copyright = '2023, Ollie Boyne'
author = 'Ollie Boyne'
release = '2023'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx_autodoc_typehints']
			  # 'sphinx.ext.intersphinx', 'sphinx.ext.imgmath', 'sphinx.ext.viewcode', 'moduleoverview']

templates_path = ['_templates']
source_dir = 'docs'
master_doc = 'index'

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_mock_imports = ["bpy", "mathutils", "bpy_extras"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
