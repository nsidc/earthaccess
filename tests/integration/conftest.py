import os
import pathlib

import earthaccess
import pytest

ACCEPTABLE_FAILURE_RATE = 10


@pytest.hookimpl()
def pytest_sessionfinish(session, exitstatus):
    """Return exit code 99 if up to N% of tests have failed.

        N = ACCEPTABLE_FAILURE_RATE

    99 was chosen arbitrarily to avoid conflict with current and future pytest error
    codes (https://docs.pytest.org/en/stable/reference/exit-codes.html), and avoid
    other exit codes with special meanings
    (https://tldp.org/LDP/abs/html/exitcodes.html).

    IMPORTANT: This is calculated against every test collected in the session, so the
    ratio will change depending on which tests are executed! E.g. executing integration
    tests and unit tests at the same time allows more tests to fail than executing
    integration tests alone.
    """
    if exitstatus != pytest.ExitCode.TESTS_FAILED:
        # Exit status 1 in PyTest indicates "Tests were collected and run but some of
        # the tests failed". In all other cases, for example "an internal error happened
        # while executing the tests", or "test execution interrupted by the user", we
        # want to defer to original pytest behavior.
        return

    failure_rate = (100.0 * session.testsfailed) / session.testscollected
    if failure_rate <= ACCEPTABLE_FAILURE_RATE:
        session.exitstatus = 99


@pytest.fixture
def mock_env(monkeypatch):
    earthaccess.__auth__ = earthaccess.Auth()
    # the original comes from github secrets
    monkeypatch.setenv("EARTHDATA_USERNAME", os.getenv("EARTHACCESS_TEST_USERNAME", ""))
    monkeypatch.setenv("EARTHDATA_PASSWORD", os.getenv("EARTHACCESS_TEST_PASSWORD", ""))


@pytest.fixture
def mock_missing_netrc(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    netrc_path = tmp_path / ".netrc"
    monkeypatch.setenv("NETRC", str(netrc_path))
    monkeypatch.delenv("EARTHDATA_USERNAME")
    monkeypatch.delenv("EARTHDATA_PASSWORD")
    # Currently, due to there being only a single, global, module-level auth
    # value, tests using different auth strategies interfere with each other,
    # so here we are deleting the auth attribute so that it doesn't interfere.
    monkeypatch.delattr(earthaccess, "__auth__", raising=False)


@pytest.fixture
def mock_netrc(mock_env, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    netrc = tmp_path / ".netrc"
    monkeypatch.setenv("NETRC", str(netrc))

    username = os.environ["EARTHDATA_USERNAME"]
    password = os.environ["EARTHDATA_PASSWORD"]

    netrc.write_text(
        f"machine urs.earthdata.nasa.gov login {username} password {password}\n"
    )
    netrc.chmod(0o600)
