#!/usr/bin/env bash

set -e

git_tag=`git describe --tags --abbrev=0`
current_version= current_version=v`cat pyproject.toml | grep version | cut -d'"' -f 2`

if [ $current_version = $git_tag ]; then
  echo "Version does match git tag"
else
  echo "Version do not match git tag, Poetry ${current_version} vs Tag: ${git_tag} "
  exit 1
fi
