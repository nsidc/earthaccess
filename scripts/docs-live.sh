#!/usr/bin/env bash
set -ex

# HACK: --no-strict is on because --dirtyreload ALWAYS throws errors. Better solution?
mkdocs serve --dev-addr 0.0.0.0:8008 --dirtyreload --no-strict
