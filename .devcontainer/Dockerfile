ARG VARIANT="3.10-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    clang-format-11 \
    cmake \
    curl \
    git \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

ENV CMAKE_GENERATOR=Ninja

ARG POETRY_VERSION=1.4
RUN pip3 install \
    "poetry==${POETRY_VERSION}"
