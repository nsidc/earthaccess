#!/bin/sh -e
set -x

ruff check --fix .
ruff format .
