#!/usr/bin/env bash

set -e
set -x

pytest tests/integration --cov=earthaccess --cov=tests/integration --cov-report=term-missing ${@} -s --tb=native --log-cli-level=INFO
bash ./scripts/lint.sh
