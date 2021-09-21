# package imports
import unittest
from unittest import mock

import responses
from earthdata.auth import Auth


class TestCreateAuth(unittest.TestCase):
    @mock.patch("builtins.input")
    @mock.patch("getpass.getpass")
    def test_create_auth_wrong_credentials(self, user_input, user_password) -> bool:
        user_input.return_value = "user"
        user_password.return_value = "pass"
        self.assertEqual(Auth().authenticated, False)

    @responses.activate
    @mock.patch("builtins.input")
    @mock.patch("getpass.getpass")
    def test_create_auth_proper_credentials(self, user_input, user_password) -> bool:
        user_input.return_value = "valid-user"
        user_password.return_value = "valid-password"
        responses.add(
            responses.POST,
            "https://cmr.earthdata.nasa.gov/legacy-services/rest/tokens",
            json={"token": {"id": "valid-token"}},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://ipinfo.io/ip",
            body="120.0.0.1",
            status=200,
        )
        # Test
        auth = Auth()
        self.assertEqual(auth.authenticated, True)
        self.assertEqual(auth.token, "valid-token")
