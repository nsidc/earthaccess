#!/usr/bin/env bash

set -ex

mypy
ruff check .
