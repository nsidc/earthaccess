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
        auth = Auth()
        logged = auth.login()
        self.assertEqual(logged, False)

    @responses.activate
    @mock.patch("builtins.input")
    @mock.patch("getpass.getpass")
    def test_auth_gets_proper_credentials(self, user_input, user_password) -> bool:
        user_input.return_value = "valid-user"
        user_password.return_value = "valid-password"
        json_response = [
            {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"},
            {"access_token": "EDL-token-2", "expiration_date": "12/16/2021"},
        ]
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/tokens",
            json=json_response,
            status=200,
        )
        # Test
        auth = Auth()
        logged = auth.login()
        self.assertEqual(logged, True)
        self.assertTrue(auth.token in json_response)

    @responses.activate
    @mock.patch("builtins.input")
    @mock.patch("getpass.getpass")
    def test_auth_can_create_proper_credentials(
        self, user_input, user_password
    ) -> bool:
        user_input.return_value = "valid-user"
        user_password.return_value = "valid-password"
        json_response = {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"}

        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/tokens",
            json=[],
            status=200,
        )

        responses.add(
            responses.POST,
            "https://urs.earthdata.nasa.gov/api/users/token",
            json=json_response,
            status=200,
        )
        # Test
        auth = Auth()
        logged = auth.login()
        self.assertEqual(logged, True)
        self.assertEqual(auth.token, json_response)
