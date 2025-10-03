# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

import datetime
import os
import sys
from importlib.metadata import version

# -- Project information -----------------------------------------------------
# The full version, including alpha/beta/rc tags

# Full version string
version = version("mast_contributor_tools")
# Short release version for Sphinx (optional)
release = version.split("+", 1)[0]


project = "mast_contributor_tools"
author = "MAST staff"
copyright = "2023, Mikulski Archive for Space Telescopes (MAST)"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    "myst_parser",  # enables Markdown (MyST)
    "sphinx.ext.autodoc",  # Auto-generate API docs from Python docstrings
    "sphinx.ext.intersphinx",  # Link cross-references to other projects' docs
    "sphinx.ext.todo",  # Support for .. todo:: directives in docs
    "sphinx.ext.coverage",  # Check doc coverage for modules/classes/functions
    "sphinx_copybutton",  # Add a "copy" button to all code blocks
    "sphinx.ext.viewcode",  # adds [source] links
    "sphinx.ext.napoleon",  # for Google/NumPy style docstrings
    "sphinx.ext.doctest",  # Run doctest examples in docs to verify they work
    "sphinx.ext.mathjax",  # Render LaTeX-style math using MathJax in HTML
    "sphinx_automodapi.automodapi",  # Astropy tool: auto-generate API docs with nice summaries
    "sphinx_automodapi.smart_resolver",  # Astropy tool: smarter cross-references for API docs
    "sphinxcontrib.spelling",  # Spell checker for docs (uses `pyenchant`)
    "sphinx_click",  # Generate docs automatically for click-based CLIs
    "sphinx.ext.autosummary",  # Generate summary tables and stub pages for documented objects (requires autosummary_generate = True)
]

autosummary_generate = True
# Suppress unnecessary warnings
suppress_warnings = [
    "myst.xref_missing",  # Suppress cross-reference missing warnings
    "myst.header",  # Suppress Non-consecutive header level increase; H1 to H3
]
# Ensure relative links are supported
myst_url_schemes = ("http", "https", "")
# Add any paths that contain templates here, relative to this directory.
# templates_path = ["_templates"]
# Add any paths that contain templates here, relative to this directory.
# templates_path = ["_templates"]

sys.path.insert(0, os.path.abspath(".."))
# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = [".rst", ".md"]

# The master toctree document.
master_doc = "index"

# Treat everything in single ` as a Python reference.
default_role = "py:obj"

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {"python": ("https://docs.python.org/", None)}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_book_theme"  # "sphinx_rtd_theme"  # "bootstrap-astropy" # "alabaster" #
html_theme_options = {
    "repository_url": "https://github.com/spacetelescope/bibcat/",
    "use_repository_button": True,  # shows the GitHub icon button
    "use_edit_page_button": True,  # adds an "edit this page" link
    "use_issues_button": True,  # adds a link to GitHub issues
    "repository_branch": "dev",  #  default branch
    "path_to_docs": "docs",  # <-- path to docs
}
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]

# By default, when rendering docstrings for classes, sphinx.ext.autodoc will
# make docs with the class-level docstring and the class-method docstrings,
# but not the __init__ docstring, which often contains the parameters to
# class constructors across the scientific Python ecosystem. The option below
# will append the __init__ docstring to the class-level docstring when rendering
# the docs. For more options, see:
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autoclass_content
autoclass_content = "both"

# -- Other options ----------------------------------------------------------
