#!/usr/bin/env sh
set -ex

mkdir -p ~/.aws

if [ "$GITHUB_ACTIONS" = "true" ]; then
  LOCALSTACK_ENDPOINT_URL="http://localhost:4566"
else
  LOCALSTACK_ENDPOINT_URL="http://localstack:4566"
fi

cat >> ~/.aws/config <<EOF




[profile localstack]
region=us-east-1
output=json
endpoint_url = $LOCALSTACK_ENDPOINT_URL


EOF
cat >> ~/.aws/credentials <<EOF
[localstack]
aws_access_key_id=test
aws_secret_access_key=test
EOF

# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
