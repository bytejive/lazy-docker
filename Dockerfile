# Build, check, and test Python module
FROM alpine:3.4
MAINTAINER John Starich <johnstarich@johnstarich.com>

RUN apk add --no-cache \
    bash \
    py-pip \
    python3 \
    python
WORKDIR /src
COPY ./setup.py /src/
RUN pip install . .[test]
COPY . /src

