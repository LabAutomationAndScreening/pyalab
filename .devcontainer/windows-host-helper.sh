#!/bin/bash

# If you are using a Windows host and you initially cloned the repository directly onto your hard drive, you may run into file permission issues when running copier updates. To avoid these, after initially building the devcontainer, run this from the repo root:
# cp .devcontainer/windows-host-helper.sh ../
# cd ..
# bash windows-host-helper.sh <git-url>

# If you're still having issues, make sure in Windows Developer Settings that you enabled Developer Mode, and also that you set your git config to have `core.autocrlf=false` and `core.symlinks=true` globally

set -euo pipefail  # Exit immediately on error

if [ -z "$BASH_VERSION" ]; then
  echo "Error: This script must be run with bash (e.g., 'bash windows-host-helper.sh')." >&2
  exit 1
fi

# Check for the git URL argument
if [ -z "$1" ]; then
    echo "Usage: $0 <git-url>"
    exit 1
fi

gitUrl="$1"

# Extract repository name (removes .git suffix if present)
repoName=$(basename "$gitUrl" .git)

echo "Repo name extracted as '$repoName'"

sudo rm -rf "./$repoName" || true
sudo rm -rf "./$repoName/*.md"
mkdir -p "./$repoName"
sudo chown -R "$(whoami):$(whoami)" "./$repoName" # TODO: see if this alone is enough to fix everything

# Create a temporary directory for cloning
tmpdir=$(mktemp -d)

# Clone the repository into a subfolder inside the temporary directory
git clone "$gitUrl" "$tmpdir/$repoName"

# Use rsync to merge all contents (including hidden files) from cloned repo to target
# -a: archive mode (preserves permissions, timestamps, etc.)
# -v: verbose
# --exclude: skip volume mount directories that should not be overwritten
echo "Syncing repository contents..."
rsync -av \
    --exclude='node_modules' \
    --exclude='.pnpm-store' \
    --exclude='.venv' \
    "$tmpdir/$repoName/" "./$repoName/"

# Clean up: remove the temporary directory
rm -rf "$tmpdir"

echo "Repository '$repoName' has been updated."
echo "Note: Volume mounts (node_modules, .pnpm-store, .venv) were preserved."
