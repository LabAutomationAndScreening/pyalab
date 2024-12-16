#!/bin/bash

mkdir ~/.aws
cat >> ~/.aws/config <<EOF
[profile localstack]
region=us-east-1
output=json
endpoint_url = http://localstack:4566
EOF
cat >> ~/.aws/credentials <<EOF
[localstack]
aws_access_key_id=test
aws_secret_access_key=test
EOF
