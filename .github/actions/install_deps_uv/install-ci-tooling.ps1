
# Set strict error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

irm https://astral.sh/uv/0.7.3/install.ps1 | iex

# Add uv to path (in github runner)
$env:Path = "C:\Users\runneradmin\.local\bin;$env:Path"

& uv --version

# Ensure that uv won't use the default system Python
$default_version = "3.12.7"

# Check if an argument is provided; if not, use the default version
if ($args.Count -eq 0) {
    $input_arg = $default_version
} else {
    $input_arg = $args[0]
}


$env:UV_PYTHON = "$input_arg"
$env:UV_PYTHON_PREFERENCE="only-system"

& uv tool install 'copier==9.6.0' --with 'copier-templates-extensions==0.3.0'

& uv tool install 'pre-commit==4.2.0'

& uv tool list
