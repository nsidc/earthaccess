from __future__ import annotations

import shutil
from pathlib import Path

import nox

DIR = Path(__file__).parent.resolve()

nox.needs_version = ">=2024.3.2"
nox.options.sessions = ["typecheck", "test_unit"]
nox.options.default_venv_backend = "uv|virtualenv"


@nox.session
def typecheck(session: nox.Session) -> None:
    """Typecheck with mypy."""
    session.install("--editable", ".[test]")
    session.run("mypy")


@nox.session
def test_unit(session: nox.Session) -> None:
    """Run the unit tests."""
    session.install("--editable", ".[test]")
    session.run("pytest", "tests/unit", *session.posargs)


@nox.session
def build_pkg(session: nox.Session) -> None:
    """Build a source distribution and binary distribution (wheel)."""
    build_path = DIR.joinpath("build")
    if build_path.exists():
        shutil.rmtree(build_path)

    session.install("build")
    session.run("python", "-m", "build")
