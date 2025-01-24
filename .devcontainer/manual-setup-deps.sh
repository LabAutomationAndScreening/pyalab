#!/usr/bin/env sh
# can pass in the full major.minor.patch version of python as an optional argument
# can set `--skip-lock` as optional argument to just install dependencies without verifying lock file
set -ex

# Ensure that uv won't use the default system Python
python_version="3.12.7"

# Parse arguments
skip_lock=false
while [ "$#" -gt 0 ]; do
    case $1 in
        --skip-lock) skip_lock=true ;;
        *) python_version="${1:-$python_version}" ;; # Take the first non-flag argument as the input
    esac
    shift
done

export UV_PYTHON="$python_version"
export UV_PYTHON_PREFERENCE=only-system

SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT_DIR="$(realpath "$SCRIPT_DIR/..")"

# Ensure that the lock file is in a good state
if [ "$skip_lock" = "false" ]; then
    uv lock --check --directory "$PROJECT_ROOT_DIR"
fi

uv sync $( [ "$skip_lock" = "false" ] && echo "--frozen" ) --directory "$PROJECT_ROOT_DIR"
uv pip list --directory "$PROJECT_ROOT_DIR"
