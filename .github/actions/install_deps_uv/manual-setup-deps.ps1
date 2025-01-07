#!/usr/bin/env pwsh
# can pass in the full major.minor.patch version of python as an optional argument

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction'] = 'Stop'


# Ensure that uv won't use the default system Python
$default_version="3.12.7"

# Check if an argument is provided; if not, use the default version
if ($args.Count -eq 0) {
    $input_arg = $default_version
} else {
    $input_arg = $args[0]
}


$env:UV_PYTHON = "$input"
$env:UV_PYTHON_PREFERENCE="only-system"

# Add uv to path (in github runner)
$env:Path = "C:\Users\runneradmin\.local\bin;$env:Path"


$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PROJECT_ROOT_DIR = Resolve-Path (Join-Path $SCRIPT_DIR "..")

# Ensure that the lock file is in a good state
& uv lock --check --directory $PROJECT_ROOT_DIR

& uv sync --frozen --directory $PROJECT_ROOT_DIR
