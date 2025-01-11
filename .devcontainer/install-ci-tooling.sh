
# can pass in the full major.minor.patch version of python as an optional argument
set -ex

curl -LsSf https://astral.sh/uv/0.5.16/install.sh | sh
uv --version
# TODO: add uv autocompletion to the shell https://docs.astral.sh/uv/getting-started/installation/#shell-autocompletion

# Ensure that uv won't use the default system Python
default_version="3.12.7"

# Use the input argument if provided, otherwise use the default value
input="${1:-$default_version}"

export UV_PYTHON="$input"
export UV_PYTHON_PREFERENCE=only-system

uv tool install 'copier==9.4.1' --with 'copier-templates-extensions==0.3.0'

uv tool install 'pre-commit==4.0.1'

uv tool list
