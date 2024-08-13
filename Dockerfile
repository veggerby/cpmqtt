# see https://github.com/micropython/micropython/wiki/Getting-Started
FROM python:3-slim-bookworm as base

FROM base AS build

RUN apt update && apt upgrade -y && apt install -y --no-install-recommends \
    build-essential \
    libreadline-dev \
    libffi-dev \
    git \
    pkg-config \
    bash

RUN /usr/local/bin/pip3 install virtualenv

WORKDIR /build/virtualenv

# Create a virtual environment and set it as the active environment

RUN virtualenv --python=$(which python3) microPython && \
    . microPython/bin/activate

WORKDIR /build/virtualenv/microPython/project/

# RUN git clone --recurse-submodules https://github.com/micropython/micropython.git
COPY lib/micropython micropython

WORKDIR /build/virtualenv/microPython/project/micropython/ports/unix

RUN make

FROM base AS final

COPY --from=build /build/virtualenv/microPython/project/micropython/ports/unix/build-standard/micropython /usr/local/bin/micropython

ENTRYPOINT [ "/usr/local/bin/micropython" ]

