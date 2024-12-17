#!/bin/bash
set -ex

sh .devcontainer/install-ci-tooling.sh

git config --global --add --bool push.autoSetupRemote true
git config --local core.symlinks true

sh .devcontainer/create-aws-profile.sh
