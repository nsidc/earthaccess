# package imports
from unittest import mock

import responses
from earthaccess import Auth, search_data
from earthaccess.auth import CLIENT_ID, Env


class TestUatEnvironmentArgument:
    @responses.activate  # This will cause the test to check that all mocked URLs are hit.
    @mock.patch("getpass.getpass", new=mock.Mock(return_value="password"))
    @mock.patch(
        "builtins.input",
        new=mock.Mock(return_value="user"),
    )
    def test_uat_login_when_uat_selected(self) -> bool:
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

        # TODO: Add a mock for CMR query?  Does it need a "CMR-HITS" field in the response?
        # responses.add(
        #     responses.GET,
        #     "https://cmr.uat.earthdata.nasa.gov/search/granules.umm_json?page_size=0",
        #     json=json_response,
        #     status=200,
        # )

        # Use Auth instance instead of the top-level (`earthaccess.`) API since this is a unit,
        # not an integration, test
        auth = Auth()

        # Check that we're not already authenticated.
        session = auth.get_session()
        headers = session.headers
        assert not auth.authenticated

        # Login
        auth.login(strategy="interactive", earthdata_environment=Env.UAT)
        assert auth.authenticated
        assert auth.token in json_response

        # Test that we are creating a session with the proper headers
        assert "User-Agent" in headers
        assert "earthaccess" in headers["User-Agent"]

        # Query CMR, and check that mock communication was with UAT CMR
        results = search_data()
        # Then possibly this:
        assert len(results) == 0
