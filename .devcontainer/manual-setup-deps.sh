#!/usr/bin/env bash
# can pass in the full major.minor.patch version of python as an optional argument
set -ex

# Ensure that uv won't use the default system Python
default_version="3.12.7"

# Use the input argument if provided, otherwise use the default value
input="${1:-$default_version}"

export UV_PYTHON="$input"
export UV_PYTHON_PREFERENCE=only-system

SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT_DIR="$(realpath $SCRIPT_DIR/..)"

# Ensure that the lock file is in a good state
uv lock --check --directory $PROJECT_ROOT_DIR

uv sync --frozen --directory $PROJECT_ROOT_DIR
