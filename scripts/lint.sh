#!/usr/bin/env bash

set -e
set -x

mypy earthaccess --disallow-untyped-defs
black earthaccess tests --check
isort --multi-line=3 --trailing-comma --force-grid-wrap=0 --combine-as --line-width 88 --check-only --thirdparty earthaccess tests
