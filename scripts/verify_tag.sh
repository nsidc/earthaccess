#!/usr/bin/env bash

# Strict mode: fail on errors, unassigned variables, and pipe failures
set -euo pipefail

echo "Validating version strings against Git tag..."

# 1. Get the git tag and strip the leading 'v'
git_tag=$(git describe --tags --abbrev=0)
core_version="${git_tag#v}"

# 2. Extract versions
# pyproject.toml: Handles 'current_version = "0.16.0"'
pyproject_version=$(grep -m 1 '^current_version[[:space:]]*=' pyproject.toml | cut -d'"' -f 2)

# CITATION.cff: Uses sed to handle both 'version: 0.16.0' and 'version: "0.16.0"'
citation_raw=$(grep -m 1 '^version:' CITATION.cff | sed -E 's/version:[[:space:]]*"?([^"]+)"?/\1/')
citation_version=$(echo "${citation_raw}" | tr -d '[:space:]')

# CHANGELOG.md: Finds the first release header like "## [v0.16.0] - 2024-10-25" and extracts the version
changelog_raw=$(grep -m 1 '^## \[v' CHANGELOG.md | sed -E 's/^## \[v([^]]+)\].*/\1/')
changelog_version=$(echo "${changelog_raw}" | tr -d '[:space:]')

# 3. Print the findings
echo "----------------------------------------"
echo "Git tag (raw):       ${git_tag}"
echo "Target version:      ${core_version}"
echo "pyproject.toml:      ${pyproject_version}"
echo "CITATION.cff:        ${citation_version}"
echo "CHANGELOG.md:        ${changelog_version}"
echo "----------------------------------------"

# 4. Compare individually against the stripped tag
mismatch=0

if [ "$pyproject_version" != "$core_version" ]; then
  echo "ERROR: pyproject.toml (${pyproject_version}) does not match Git tag (${core_version})!"
  mismatch=1
fi

if [ "$citation_version" != "$core_version" ]; then
  echo "ERROR: CITATION.cff (${citation_version}) does not match Git tag (${core_version})!"
  mismatch=1
fi

if [ "$changelog_version" != "$core_version" ]; then
  echo "ERROR: CHANGELOG.md top entry (${changelog_version}) does not match Git tag (${core_version})!"
  echo "       (Did bump-my-version fail to find the '## [Unreleased]' header?)"
  mismatch=1
fi

# 5. Exit with the proper code
if [ $mismatch -ne 0 ]; then
  echo "Version validation failed! See errors above."
  exit 1
fi

echo "✅ All version strings and documentation match the Git tag."
