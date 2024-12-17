#!/bin/bash
set -ex

sh .devcontainer/install-ci-tooling.sh

git config --global --add --bool push.autoSetupRemote true

sh .devcontainer/create-aws-profile.sh
