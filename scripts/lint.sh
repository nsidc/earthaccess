#!/usr/bin/env bash

set -e
set -x

mypy earthaccess --disallow-untyped-defs
ruff check earthaccess tests
