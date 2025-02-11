class LoginStrategyUnavailable(Exception):
    """The selected login strategy was skipped.

    This should be raised when a login strategy can't be attempted, for example because
    "environment" was selected but the envvars are not populated.

    DO NOT raise this exception when a login strategy is attempted and failed, for
    example because credentials were rejected.
    """
    pass


class LoginAttemptFailure(Exception):
    """The login attempt failed."""
    pass
