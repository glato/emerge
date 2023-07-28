FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y git graphviz graphviz-dev python3-pip \
    && yes | pip install emerge-viz

USER 1002

ENTRYPOINT ["emerge", "-c"]