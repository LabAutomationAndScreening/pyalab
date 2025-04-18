# For MyBinder
# Following documentation https://mybinder.readthedocs.io/en/latest/tutorials/dockerfile.html
FROM python:3.12.7-bookworm

RUN python3 -m pip install --no-cache-dir --root-user-action=ignore --disable-pip-version-check notebook==7.3.1 jupyterlab==4.3.4

ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}

# Make sure the contents of our repo are in ${HOME}
COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}

WORKDIR /home/jovyan

RUN python3 -m pip install --no-cache-dir --root-user-action=ignore --disable-pip-version-check -e .


ENTRYPOINT []
