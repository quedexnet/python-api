#!/bin/bash

if [ ! -d "venv" ]; then
  virtualenv --no-site-packages venv
fi

. venv/bin/activate
pip install -r requirements

python -m unittest discover
