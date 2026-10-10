"""Sphinx configuration for nuwe-cmadaas-python documentation."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_ext"))

project = "nuwe-cmadaas-python"
copyright = "2019-2026, Wang Dapeng at cemc-oper"
author = "perillaroc"

extensions = [
    # Keep these until the old IPython directives have been migrated.
    "IPython.sphinxext.ipython_console_highlighting",
    "IPython.sphinxext.ipython_directive",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "myst_nb",
    "support_matrix",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "myst-nb",
}
myst_enable_extensions = ["colon_fence"]
nb_execution_mode = "force"

language = "zh_CN"
exclude_patterns = ["_build"]

html_theme = "pydata_sphinx_theme"
html_title = "nuwe-cmadaas"
html_theme_options = {
    "github_url": "https://github.com/perillaroc/nuwe-cmadaas-python",
    "header_links_before_dropdown": 4,
    "navigation_depth": 3,
    "show_nav_level": 2,
    "show_toc_level": 2,
    "navbar_align": "left",
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "secondary_sidebar_items": ["page-toc", "edit-this-page"],
    "use_edit_page_button": True,
}
html_context = {
    "github_user": "perillaroc",
    "github_repo": "nuwe-cmadaas-python",
    "github_version": "main",
    "doc_path": "docs/source",
}
