#!/bin/bash

sh .devcontainer/install-ci-tooling.sh

# the global pytest install can cause problems if people forget to activate their venv
rm /usr/local/py-utils/bin/pytest

git config --global --add --bool push.autoSetupRemote true

sh .devcontainer/create-aws-profile.sh
