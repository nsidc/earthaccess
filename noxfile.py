from __future__ import annotations

import os
import shutil
from pathlib import Path

import nox

DIR = Path(__file__).parent.resolve()

nox.needs_version = ">=2024.3.2"
nox.options.sessions = ["typecheck", "tests"]
nox.options.default_venv_backend = "uv|virtualenv"


@nox.session
def typecheck(session: nox.Session) -> None:
    """Typecheck with mypy."""
    session.install("--editable", ".[test]")
    session.run("mypy")


@nox.session
def tests(session: nox.Session) -> None:
    """Run the unit tests."""
    session.install("--editable", ".[test]")
    session.run(
        "pytest",
        "tests/unit",
        "-rxXs",  # Show provided reason in summary for (x)fail, (X)pass, and (s)kipped tests
        *session.posargs,
    )


@nox.session(name="test-min-deps", python="3.11", venv_backend="uv")
def test_min_deps(session: nox.Session) -> None:
    """Run the unit tests using the lowest compatible version of all direct dependencies."""
    session.install("--resolution", "lowest-direct", "--editable", ".[test]")
    session.run(
        "pytest",
        "tests/unit",
        "-rxXs",  # Show provided reason in summary for (x)fail, (X)pass, and (s)kipped tests
        *session.posargs,
    )


@nox.session(name="integration-tests")
def integration_tests(session: nox.Session) -> None:
    """Run the integration tests."""
    session.install("--editable", ".[test]")
    session.run(
        "pytest",
        "tests/integration",
        "-rxXs",  # Show provided reason in summary for (x)fail, (X)pass, and (s)kipped tests
        *session.posargs,
        env=dict(
            EARTHDATA_USERNAME=os.environ["EARTHDATA_USERNAME"],
            EARTHDATA_PASSWORD=os.environ["EARTHDATA_PASSWORD"],
        ),
    )


@nox.session(name="build-pkg")
def build_pkg(session: nox.Session) -> None:
    """Build a source distribution and binary distribution (wheel)."""
    build_path = DIR.joinpath("build")
    if build_path.exists():
        shutil.rmtree(build_path)

    session.install("build")
    session.run("python", "-m", "build")


@nox.session(name="serve-docs")
def serve_docs(session: nox.Session) -> None:
    """Build the documentation and serve it."""
    session.install("--editable", ".[docs]")
    session.run("mkdocs", "serve", *session.posargs)
