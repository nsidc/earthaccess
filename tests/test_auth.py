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
        json_response = {"token": {"id": "valid-token"}}
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/tokens",
            json=json_response,
            status=200,
        )
        # Test
        auth = Auth()
        self.assertEqual(auth.authenticated, True)
        self.assertEqual(auth.token, json_response)
