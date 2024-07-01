#!/usr/bin/env bash

set -e
set -x

pytest --cov=earthaccess --cov=tests/integration --cov-report=term-missing ${@} -s --tb=native --log-cli-level=INFO
