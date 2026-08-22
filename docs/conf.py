# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-python-package-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from typing import Literal

from sphinx.application import Sphinx

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pyalab"
copyright = "2024, Eli Fine"  # noqa: A001  # Sphinx requires this exact variable name
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


def autodoc_skip_member(  # noqa: PLR0913 # Sphinx requires all these parameters in the callback signature
    app: Sphinx,  # noqa: ARG001 # signature required by Sphinx autodoc-skip-member event
    what: Literal["module", "class", "exception", "function", "method", "attribute"],  # noqa: ARG001 # signature required by Sphinx autodoc-skip-member event
    name: str,
    obj: object,  # noqa: ARG001 # signature required by Sphinx autodoc-skip-member event
    skip: bool,
    options: dict[str, bool],  # noqa: ARG001 # signature required by Sphinx autodoc-skip-member event
) -> bool:
    # Exclude specific attributes by name
    if name in ["model_config", "model_post_init"]:
        return True  # Skip this method from documentation
    return skip


def setup(app: Sphinx):
    _ = app.connect("autodoc-skip-member", autodoc_skip_member)
