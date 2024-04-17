#!/usr/bin/env bash

set -ex

mypy earthaccess stubs tests
ruff check .
