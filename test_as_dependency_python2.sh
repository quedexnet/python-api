#!/bin/bash

set -e

if [ ! -d "venv" ]; then
  virtualenv --no-site-packages venv-dep
fi

. venv-dep/bin/activate
pip install .

python -m unittest discover tests

