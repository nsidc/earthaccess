#!/usr/bin/env bash

set -x
pytest tests/integration --cov=earthaccess --cov-report=term-missing "${@}" --capture=no --tb=native --log-cli-level=INFO
RET=$?
set +x

set -e
# NOTE: 99 is a special return code we selected for this case, it has no other meaning.
if [[ $RET == 99 ]]; then
    echo -e "\e[0;31mWARNING: The integration test suite has been permitted to return 0 because the failure rate was less than a hardcoded threshold.\e[0m"
    echo "For more details, see conftest.py."
    exit 0
elif [[ $RET != 0 ]]; then
    exit $RET
fi
