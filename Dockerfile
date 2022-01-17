FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:0

RUN apt update && apt install -y \
    curl wget vim python3 python3-pip firefox \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz -O /tmp/gecko.tar.gz
RUN tar xvf /tmp/gecko.tar.gz
RUN mv geckodriver /usr/local/bin

COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
RUN pip3 install -e .
