FROM mcr.microsoft.com/vscode/devcontainers/universal:2.9.0-focal

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -y && apt-get install -y \
    "bash-completion=$(apt-cache madison bash-completion | awk '{print $3}' | grep '^1:2.10' | head -n 1)" --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create the venv folder and set permissions for anyone to modify---this is necessary to be able to break out the venv folder as a separate docker volume for better performance on Windows hosts
ARG REPO_NAME=copier-base-template
ENV VENV_PATH=/workspaces/${REPO_NAME}/.venv
RUN mkdir -p /workspace && \
    mkdir -p ${VENV_PATH} && \
    chmod -R 777 /workspaces ${VENV_PATH} && \
    chgrp -R 0 /workspaces ${VENV_PATH}

# SSH
EXPOSE 2222
