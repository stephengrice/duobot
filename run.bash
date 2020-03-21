#!/bin/bash

if [ $(command -v python) ]; then
  python src/duobot.py
elif [ $(command -v python3) ]; then
  python3 src/duobot.py
else
  echo Error: Python not installed.
  echo Please install python or python3 to use this program.
fi
