.PHONY: help

# Shell that make should use
SHELL:=bash

# Capture git branch and hash information
# https://stackoverflow.com/questions/43008842/capture-git-branch-name-in-makefile-variable
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
HASH := $(shell git rev-parse HEAD)

# - to suppress if it doesn't exist
-include make.env

help:
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
# adds anything that has a double # comment to the phony help list
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ".:*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

python-three-eight: ## setup python3.8 virtual environment using poetry
	poetry env use python3.8
	PIP_REQUIRE_VENV=0 poetry install

python-three-nine: ## setup python3.9 virtual environment using poetry
	poetry env use python3.9
	PIP_REQUIRE_VENV=0 poetry install

python-three-ten: ## setup python3.10 virtual environment using poetry
	poetry env use python3.10
	PIP_REQUIRE_VENV=0 poetry install

pre-commit:  ## setup pre-commit within poetry
	poetry run pre-commit install

lint: ## lint the code
	bash scripts/lint.sh

format: ## format the code
	bash scripts/format.sh

test: ## lint the code
	bash scripts/test.sh

docs-live: ## make live docs
	bash scripts/docs-live.sh

install: ## uninstall and install package with python
	poetry remove ./earthaccess
	poetry add ./earthaccess
