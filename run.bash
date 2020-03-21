#!/bin/bash

ENTRY_POINT=src/main/duobot.py

if [ $(command -v python) ]; then
  python $ENTRY_POINT
elif [ $(command -v python3) ]; then
  python3 $ENTRY_POINT
else
  echo Error: Python not installed.
  echo Please install python or python3 to use this program.
fi
