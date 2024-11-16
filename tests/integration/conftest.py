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
def mock_missing_netrc(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    netrc_path = tmp_path / ".netrc"
    monkeypatch.setenv("NETRC", str(netrc_path))
    monkeypatch.delenv("EARTHDATA_USERNAME", raising=False)
    monkeypatch.delenv("EARTHDATA_PASSWORD", raising=False)
    # Currently, due to there being only a single, global, module-level auth
    # value, tests using different auth strategies interfere with each other,
    # so here we are monkeypatching a new, unauthenticated Auth object.
    auth = earthaccess.Auth()
    monkeypatch.setattr(earthaccess, "_auth", auth)
    monkeypatch.setattr(earthaccess, "__auth__", auth)


@pytest.fixture
def mock_netrc(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    netrc = tmp_path / ".netrc"
    monkeypatch.setenv("NETRC", str(netrc))

    if "EARTHDATA_USERNAME" in os.environ and "EARTHDATA_PASSWORD" in os.environ:
        username = os.environ["EARTHDATA_USERNAME"]
        password = os.environ["EARTHDATA_PASSWORD"]
    else:
        raise Exception("Unable to mock a .netrc without EARTHDATA_USERNAME and EARTHDATA_PASSWORD environment variables")

    netrc.write_text(
        f"machine urs.earthdata.nasa.gov login {username} password {password}\n"
    )
    netrc.chmod(0o600)
