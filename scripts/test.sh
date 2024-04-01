#!/usr/bin/env bash

set -e
set -x

pytest tests/unit --cov=earthaccess --cov=tests --cov-report=term-missing "${@}" -s --tb=native --log-cli-level=INFO
bash ./scripts/lint.sh
