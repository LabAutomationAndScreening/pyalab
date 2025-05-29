#!/bin/bash
set -ex

python .devcontainer/install-ci-tooling.py

git config --global --add --bool push.autoSetupRemote true
git config --local core.symlinks true

sh .devcontainer/create-aws-profile.sh
