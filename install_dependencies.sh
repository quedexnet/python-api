#!/bin/sh

case "$BUILD_CONFIGURATION" in
    "main") pip install -r requirements
            ;;
    "dependency") pip install .
                  ;;
    *) echo "Invalid BUILD_CONFIGURATION '$BUILD_CONFIGURATION'."
       exit 1
       ;;
esac

