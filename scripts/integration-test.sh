#!/usr/bin/env bash
set -ex

pytest tests/integration --cov=earthaccess --cov=tests/integration --cov-report=term-missing ${@} --capture=no --tb=native --log-cli-level=INFO

bash ./scripts/lint.sh
