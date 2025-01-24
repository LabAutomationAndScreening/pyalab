[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![Actions status](https://github.com/LabAutomationAndScreening/pyalab/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/LabAutomationAndScreening/pyalab/actions)
[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/LabAutomationAndScreening/pyalab)
[![PyPI Version](https://img.shields.io/pypi/v/pyalab.svg)](https://pypi.org/project/pyalab/)
[![Downloads](https://pepy.tech/badge/pyalab)](https://pepy.tech/project/pyalab)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyalab.svg)](https://pypi.org/project/pyalab/)
[![Codecov](https://codecov.io/gh/LabAutomationAndScreening/pyalab/branch/main/graph/badge.svg)](https://codecov.io/gh/LabAutomationAndScreening/pyalab)
[![Documentation Status](https://readthedocs.org/projects/pyalab/badge/?version=latest)](https://pyalab.readthedocs.io/en/latest/?badge=latest)

# Usage
Pyalab is a way to use Python to generate programs for Vialab---the software that controls the Integra ASSIST Plus automated liquid handling robot.

Documentation is hosted on [ReadTheDocs](https://pyalab.readthedocs.io/en/latest/?badge=latest).

Don't want to figure out how to install Python on your computer?  No problem! Use this MyBinder link to launch a free online environment (no sign-up required) where you can use `pyalab` to create and then download your Vialab programs. [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/LabAutomationAndScreening/pyalab/main?labpath=docs%2Fcreate_vialab_program.ipynb)

# Development
This project has a dev container. If you already have VS Code and Docker installed, you can click the badge above or [here](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/LabAutomationAndScreening/pyalab) to get started. Clicking these links will cause VS Code to automatically install the Dev Containers extension if needed, clone the source code into a container volume, and spin up a dev container for use.







## Updating from the template
This repository uses a copier template. To pull in the latest updates from the template, use the command:
`copier update --trust --conflict rej --defaults`
