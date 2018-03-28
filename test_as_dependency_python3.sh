#!/bin/bash

set -e

if [ ! -d "venv3" ]; then
  python3 -m venv venv3-dep
fi

. venv3-dep/bin/activate
pip install .

python -m unittest discover tests

