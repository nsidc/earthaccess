# package imports
from unittest import mock

import responses
from earthaccess import Auth
from earthaccess.auth import CLIENT_ID


class TestUatEnvironmentArgument:
    @responses.activate
    @mock.patch("getpass.getpass", new=mock.Mock(return_value="password"))
    @mock.patch(
        "builtins.input",
        new=mock.Mock(return_value="user"),
    )
    def test_uat_is_requested_when_uat_selected(self) -> bool:
        """Test the correct env is queried based on what's selected at login-time."""
        json_response = [
            {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"},
            {"access_token": "EDL-token-2", "expiration_date": "12/16/2021"},
        ]
        responses.add(
            responses.GET,
            "https://uat.urs.earthdata.nasa.gov/api/users/tokens",
            json=json_response,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://uat.urs.earthdata.nasa.gov/profile",
            json={"email_address": "test@test.edu"},
            status=200,
        )
        responses.add(
            responses.GET,
            f"https://uat.urs.earthdata.nasa.gov/api/users/user?client_id={CLIENT_ID}",
            json={},
            status=200,
        )

        # Test
        # Login
        # TODO: Can we use the top-level API? Why do other tests manually create
        # an Auth instance instead of:
        #     earthaccess.login(strategy=..., earthdata_environment=Env.UAT)
        auth = Auth()
        auth.login(strategy="interactive")

        # Check that mock communication was with UAT EDL
        ...

        # Query CMR
        ...

        # Check that mock communication was with UAT CMR
        ...
