#!/bin/sh -e
set -x

ruff check --fix earthaccess tests
ruff format earthaccess tests
