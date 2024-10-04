#!/usr/bin/env bash

set -e

git_tag=`git describe --tags --abbrev=0`
current_version= current_version=v`cat pyproject.toml | grep -m 1 version | cut -d'"' -f 2`

echo "${git_tag} ${current_version}"

if [ $current_version == $git_tag ]; then
  echo "Version does match git tag"
else
  echo "Version does not match git tag! pyproject.toml: ${current_version} vs Tag: ${git_tag} "
  exit 1
fi
