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
    """Run the typechecker."""
    session.install(".[test]")
    session.run("mypy")


@nox.session
def test_unit(session: nox.Session) -> None:
    """Run the unit tests."""
    session.install(".[test]")
    session.run(*_test_cmd("tests/unit"), *session.posargs)


@nox.session
def test_integration(session: nox.Session) -> None:
    """Run the unit tests."""
    session.install(".[test]")
    session.run(*_test_cmd("tests/integration"), *session.posargs)


@nox.session(reuse_venv=True)
def docs_build(session: nox.Session) -> None:
    """Build the docs."""
    session.install(".[docs]")
    session.run("mkdocs", "build")


@nox.session(reuse_venv=True)
def docs_serve(session: nox.Session) -> None:
    """Serve the docs for development."""
    session.install(".[docs]")

    session.run(
        "mkdocs",
        "serve",
        "--dev-addr",
        "0.0.0.0:8008",
        "--dirtyreload",
        # HACK: --no-strict is on because --dirtyreload ALWAYS throws errors. Better
        # solution?
        "--no-strict",
    )


@nox.session
def pkg_build(session: nox.Session) -> None:
    """Build a source distribution and binary distribution (wheel)."""
    build_path = DIR.joinpath("dist")
    if build_path.exists():
        shutil.rmtree(build_path)

    session.install("build")
    session.run("python", "-m", "build")


def _test_cmd(tests_dir: str) -> list[str]:
    return [
        "pytest",
        tests_dir,
        "--cov=earthaccess",
        f"--cov={tests_dir}",
        "--cov-report=term-missing",
        "--capture=no",
        "--tb=native",
        "--log-cli-level=INFO",
    ]
