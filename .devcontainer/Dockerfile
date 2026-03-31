# base image tags available at https://mcr.microsoft.com/v2/devcontainers/universal/tags/list
# added the platform flag to override any local settings since this image is only compatible with linux/amd64. since this image is only x64 compatible, suppressing the hadolint rule
# hadolint ignore=DL3029
FROM --platform=linux/amd64 mcr.microsoft.com/devcontainers/universal:5.1.5-noble

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# temporary hack until yarn updates its GPG key
RUN rm /etc/apt/sources.list.d/yarn.list || true && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor | tee /etc/apt/keyrings/yarn-archive-keyring.gpg > /dev/null

RUN apt-get update -y && apt-get install -y \
    "bash-completion=$(apt-cache madison bash-completion | awk '{print $3}' | grep '^1:2.11' | head -n 1)" --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create the venv folder and set permissions for anyone to modify---this is necessary to be able to break out the venv folder as a separate docker volume for better performance on Windows hosts
ARG REPO_NAME=copier-base-template
ENV VENV_PATH=/workspaces/${REPO_NAME}/.venv
RUN mkdir -p /workspaces && \
    mkdir -p ${VENV_PATH} && \
    chmod -R 777 /workspaces ${VENV_PATH} && \
    chgrp -R 0 /workspaces ${VENV_PATH}

# SSH
EXPOSE 2222
