"""Helper script that automatically skips the yamlfmt pre-commit hook on Windows.

This is not intended to be called directly.  It is configured to be called by
pre-commit via the configuration in .pre-commit-config.yml for the yamlfmt hook.

Due to https://github.com/google/yamlfmt/issues/263, comments in yaml files are
not handled properly under Windows, so any Windows user that causes yamlfmt to
format yaml files will cause CI build failure because we build under Linux, and
the resulting format will differ, causing file changes during the pre-commit
step, causing build failure.

Therefore, this script avoids calling yamlfmt (via pre-commit) when running on
Windows.
"""

import platform
import subprocess
import sys

if platform.system() != "Windows":
    sys.exit(subprocess.call(["yamlfmt", *sys.argv[1:]]))
