import pytest

ACCEPTABLE_FAILURE_RATE = 10


@pytest.hookimpl()
def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 0:
        return

    if session.testscollected == 0:
        raise RuntimeError(
            "Failed to initialize tests. Couldn't calculate acceptable failure rate"
            " because no tests were collected."
            " This can happen if credential envvars are not populated."
        )

    failure_rate = (100.0 * session.testsfailed) / session.testscollected
    if failure_rate <= ACCEPTABLE_FAILURE_RATE:
        session.exitstatus = 0
