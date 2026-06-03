#!/bin/bash
set -ex

# For some reason the directory is not setup correctly and causes build of devcontainer to fail since
# it doesn't have access to the workspace directory. This can normally be done in post-start-command
script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH='' cd -- "$script_dir/.." && pwd)"
git config --global --add safe.directory "$repo_root"

sh .devcontainer/on-create-command-boilerplate.sh
# install json5 for merging claude settings.  TODO: consider if we can install json5 globally...or somehow eliminate this dependency
mkdir -p "$repo_root/.claude"
chmod -R ug+rwX "$repo_root/.claude"
chgrp -R 0 "$repo_root/.claude" || true
npm --prefix "$repo_root/.claude" ci

# Install beads for use in Claude planning
npm install -g @beads/bd@0.57.0 # no specific reason for this version, just pinning for best practice

pre-commit install --install-hooks

python .devcontainer/manual-setup-deps.py --optionally-check-lock
