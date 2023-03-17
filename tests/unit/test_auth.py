# package imports
import unittest
from unittest import mock

import pytest
import responses
from earthaccess import Auth


class TestCreateAuth(unittest.TestCase):
    @responses.activate
    @mock.patch("getpass.getpass")
    @mock.patch("builtins.input")
    def test_auth_gets_proper_credentials(self, user_input, user_password) -> bool:
        user_input.return_value = "user"
        user_password.return_value = "password"
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
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={"email_address": "test@test.edu"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/user?client_id=ntD0YGC_SM3Bjs-Tnxd7bg",
            json={},
            status=200,
        )

        # Test
        auth = Auth()
        self.assertEqual(auth.authenticated, False)
        auth.login(strategy="interactive")
        self.assertEqual(auth.authenticated, True)
        self.assertTrue(auth.token in json_response)

    @responses.activate
    @mock.patch("getpass.getpass")
    @mock.patch("builtins.input")
    def test_auth_can_create_proper_credentials(
        self, user_input, user_password
    ) -> bool:
        user_input.return_value = "user"
        user_password.return_value = "password"
        json_response = {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"}

        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/tokens",
            json=[],
            status=200,
        )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/user?client_id=ntD0YGC_SM3Bjs-Tnxd7bg",
            json={},
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
        auth.login(strategy="interactive")
        self.assertEqual(auth.authenticated, True)
        self.assertEqual(auth.password, "password")
        self.assertEqual(auth.token, json_response)

    @responses.activate
    @mock.patch("getpass.getpass")
    @mock.patch("builtins.input")
    def test_auth_fails_for_wrong_credentials(self, user_input, user_password) -> bool:
        user_input.return_value = "bad_user"
        user_password.return_value = "bad_password"
        json_response = {"error": "wrong credentials"}

        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/tokens",
            json=json_response,
            status=401,
        )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json=json_response,
            status=401,
        )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/user?client_id=ntD0YGC_SM3Bjs-Tnxd7bg",
            json=json_response,
            status=401,
        )
        responses.add(
            responses.POST,
            "https://urs.earthdata.nasa.gov/api/users/token",
            json=json_response,
            status=401,
        )
        # Test
        auth = Auth()
        auth.login(strategy="interactive")
        with pytest.raises(Exception) as e_info:
            print(e_info)
            self.assertEqual(auth.authenticated, False)
            self.assertEqual(e_info, Exception)
            self.assertEqual(auth.password, "password")
            self.assertEqual(auth.token, json_response)
