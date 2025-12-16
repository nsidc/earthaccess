class LoginStrategyUnavailable(Exception):
    """The selected login strategy was skipped.

    This should be raised when a login strategy can't be attempted, for example because
    "environment" was selected but the envvars are not populated.

    DO NOT raise this exception when a login strategy is attempted and fails. For
    example, this exception would not be thrown when credentials were rejected;
    a `LoginAttemptFailure` should be thrown instead.
    """

    pass


class LoginAttemptFailure(Exception):
    """The login attempt failed.

    This should be raised when a login attempt fails, for example, because
    the user's credentials were rejected.

    DO NOT raise this exception when a login strategy can't be attempted. For
    example, this exception would not be thrown when "environment" was selected
    but the envvars are not populated; a `LoginStrategyUnavailable` should be
    thrown instead.
    """

    pass


class DownloadFailure(Exception):
    """The download attempt failed.

    This should be raised when a download attempt fails, for example, because
    the file could not be retrieved or the download process was interrupted.
    """

    pass


class ServiceOutage(Exception):
    """A service outage has been detected.

    This should be raised when Earthdata services are unavailable or experiencing
    outages that prevent normal operations.
    """

    pass


class EulaNotAccepted(DownloadFailure):
    """The user has not accepted the EULA.

    This should be raised when a user attempts to access data that requires
    EULA acceptance, but they have not accepted the EULA.
    """

    pass
