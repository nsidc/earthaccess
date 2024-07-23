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
