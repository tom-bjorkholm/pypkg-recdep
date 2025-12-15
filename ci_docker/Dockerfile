FROM registry.gitlab.com/python-devs/ci-images:active
LABEL python.ci-image.authors="Tom Björkholm <klausuler_linnet0q@icloud.com>"

ARG SERIES
ENV SERIES=${SERIES}

ENV PATH="/usr/local/bin:$PATH"


# Set Debian front-end to non-interactive so that apt doesn't ask for
# prompts later.
ENV  DEBIAN_FRONTEND=noninteractive

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

COPY pip_installs.zsh /tmp/pip_installs.zsh
RUN chmod +x /tmp/pip_installs.zsh
RUN zsh /tmp/pip_installs.zsh
RUN rm /tmp/pip_installs.zsh

# Switch to runner user and set the workdir.
USER runner
WORKDIR /home/runner
