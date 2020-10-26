#!/bin/bash

sudo apt update -y && sudo apt install -y wget firefox

if [ $(command -v pip) ]; then
  PIP=pip
elif [ $(command -v pip3) ]; then
  PIP=pip3
else
  echo Error: Pip is not installed.
  echo Please install pip to continue.
  exit 1
fi

$PIP install -r requirements.txt

pushd .
cd /tmp
wget https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
tar xvf geckodriver-v0.26.0-linux64.tar.gz
sudo cp geckodriver /usr/bin
popd
