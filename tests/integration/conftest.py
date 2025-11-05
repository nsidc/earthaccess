import os
import pathlib

import earthaccess
import pytest


@pytest.fixture
def mock_missing_netrc(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    netrc_path = tmp_path / ".netrc"
    monkeypatch.setenv("NETRC", str(netrc_path))
    monkeypatch.delenv("EARTHDATA_USERNAME")
    monkeypatch.delenv("EARTHDATA_PASSWORD")
    # Currently, due to there being only a single, global, module-level auth
    # value, tests using different auth strategies interfere with each other,
    # so here we are monkeypatching a new, unauthenticated Auth object.
    auth = earthaccess.Auth()
    monkeypatch.setattr(earthaccess, "_auth", auth)
    monkeypatch.setattr(earthaccess, "__auth__", auth)


@pytest.fixture  # pyright: ignore[reportCallIssue]
def mock_netrc(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    netrc = tmp_path / ".netrc"
    monkeypatch.setenv("NETRC", str(netrc))

    username = os.environ["EARTHDATA_USERNAME"]
    password = os.environ["EARTHDATA_PASSWORD"]

    netrc.write_text(
        f"machine urs.earthdata.nasa.gov login {username} password {password}\n"
    )
    netrc.chmod(0o600)
