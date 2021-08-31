#!/usr/bin/env bash

set -e

# https://python-poetry.org/docs/libraries/
# https://python-poetry.org/docs/cli/#publish
poetry publish  --build
