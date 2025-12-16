FROM registry.gitlab.com/python-devs/ci-images:active
LABEL tombjorkholm.py-ci-image.authors="Tom Björkholm <klausuler_linnet0q@icloud.com>"

USER root
WORKDIR /

ARG SERIES
ENV SERIES=${SERIES}

ENV PATH="/usr/local/bin:$PATH"


# Set Debian front-end to non-interactive so that apt doesn't ask for
# prompts later.
ENV  DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /var/lib/apt/lists/partial && chmod 700 /var/lib/apt/lists/partial
RUN mkdir -p /var/cache/apt/archives/partial && chmod 700 /var/cache/apt/archives/partial

RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    libssl-dev \
    libffi-dev \
    git \
    zsh \
    curl \
    wget 

RUN apt-get install -y grep coreutils sed gawk findutils
RUN apt-get install -y make tar bzip2 gzip zip

COPY pip_installs.zsh /tmp/pip_installs.zsh
RUN chmod +x /tmp/pip_installs.zsh
RUN zsh /tmp/pip_installs.zsh
RUN rm /tmp/pip_installs.zsh

# Switch to runner user and set the workdir.
USER runner
WORKDIR /home/runner
