#!/bin/bash

if [ $(command -v pip) ]; then
  PIP=pip
elif [ $(command -v pip3) ]; then
  PIP=pip3
else
  echo Error: Pip is not installed.
  echo Please install pip to continue.
fi

$PIP install -r requirements.txt
