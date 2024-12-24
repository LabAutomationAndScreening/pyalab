# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from sphinx.application import Sphinx
from typing import Any, Literal
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pyalab"
copyright = "2024, Eli Fine"
author = "Eli Fine"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxcontrib.autodoc_pydantic",
]


autodoc_pydantic_model_undoc_members = False
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_settings_hide_paramlist = True
autodoc_pydantic_settings_signature_prefix = ""
autodoc_pydantic_model_member_order = "bysource"
autodoc_pydantic_settings_show_field_summary = False
autodoc_member_order = "bysource"
autodoc_pydantic_inherited_members = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]


# skip generic pydantic BaseModel methods
def autodoc_skip_member(  # noqa: PLR0913 # this is a lot of arguments, but it's how Sphinx requires the signature to be
    app: Sphinx,
    what: Literal["module", "class", "exception", "function", "method", "attribute"],
    name: str,
    obj: Any,
    skip: bool,
    options: dict[str, bool],
):
    # Exclude specific attributes by name
    if name in ["model_config", "model_post_init"]:
        return True  # Skip this method from documentation
    return skip


def setup(app: Sphinx):
    _ = app.connect("autodoc-skip-member", autodoc_skip_member)
