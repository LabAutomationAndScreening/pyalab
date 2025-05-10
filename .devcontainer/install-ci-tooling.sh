
# can pass in the full major.minor.patch version of python as an optional argument
set -ex





curl -LsSf https://astral.sh/uv/0.7.3/install.sh | sh
uv --version
# TODO: add uv autocompletion to the shell https://docs.astral.sh/uv/getting-started/installation/#shell-autocompletion

# Set to the system version of Python3 by default
default_version=$(python3 -c "import sys; print ('.'.join((str(x) for x in sys.version_info[:3])))")

# Use the input argument if provided, otherwise use the default value
input="${1:-$default_version}"

export UV_PYTHON="$input"
export UV_PYTHON_PREFERENCE=only-system

uv tool install 'copier==9.6.0' --with 'copier-templates-extensions==0.3.0'

uv tool install 'pre-commit==4.2.0'

uv tool list
