#!/bin/bash
set -e
cd ~/led-strip

if [ ! -d venv ]; then
    python3 -m venv venv
fi

source venv/bin/activate
python led.py
