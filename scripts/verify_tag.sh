#!/usr/bin/env bash

set -e

# Get the git tag (this works in CI because the release triggers a checkout at the tag)
git_tag=$(git describe --tags --abbrev=0)

# With VCS-based versioning (hatch-vcs), the git tag IS the version source.
# Verify the tag matches the version tracked in CITATION.cff, which bump-my-version updates.
citation_version=v$(grep -m 1 '^version:' CITATION.cff | cut -d'"' -f 2)

echo "Git tag: ${git_tag}"
echo "CITATION.cff version: ${citation_version}"

if [ "$citation_version" == "$git_tag" ]; then
  echo "Version matches git tag"
else
  echo "Version does not match git tag! CITATION.cff: ${citation_version} vs Tag: ${git_tag}"
  exit 1
fi
