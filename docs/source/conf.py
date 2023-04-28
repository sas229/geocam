# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.append(os.path.abspath("../../src/geocam/"))

# -- Project information -----------------------------------------------------

project = 'geocam'
copyright = '2023, Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane'
author = 'Hilario Greggi, Sam Stanier, Zewen Wang, Wenhan Du, Barry Lehane'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "autoapi.extension",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "sphinxcontrib.bibtex",
    "sphinx.ext.todo",
    "sphinx.ext.intersphinx"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_theme_options = {
    "body_max_width": "100%",
    "includehidden": True,
    "collapse_navigation": True,
}
html_show_sourcelink = False

# Automatic API documentation.
autodoc_typehints = "signature"
add_module_names = True
math_number_all = False
autoapi_dirs = ["../../src/geocam"]
autoapi_options = [
    "members",
    "show-inheritance",
    "show-module-summary",
    # 'private-members',
    "special-members",
    "imported-members",
]
autoapi_keep_files = True
suppress_warnings = ["autoapi"]
autoapi_add_toctree_entry = False
autoapi_python_class_content = "init"
autoapi_template_dir = "_templates/autoapi"
autoapi_member_order = "groupwise"

# References.
bibtex_bibfiles = ["refs.bib"]
bibtex_default_style = "plain"

# To do.
todo_include_todos = True

# Figure numbering.
numfig = True

# Intersphinx.
intersphinx_mapping = {
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}
myst_url_schemes = [
    "http",
    "https",
]
