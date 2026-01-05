# package imports
import logging
import os
import unittest
from unittest import mock

import pytest
import responses
from earthaccess import Auth
from earthaccess.exceptions import LoginAttemptFailure

logger = logging.getLogger(__name__)


class TestCreateAuth(unittest.TestCase):
    @responses.activate
    @mock.patch("getpass.getpass")
    @mock.patch("builtins.input")
    def test_auth_gets_proper_credentials(self, user_input, user_password):
        user_input.return_value = "user"
        user_password.return_value = "password"
        json_response = {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"}

        responses.add(
            responses.POST,
            "https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
            json=json_response,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={"email_address": "test@test.edu"},
            status=200,
        )

        # Test
        auth = Auth()
        self.assertEqual(auth.authenticated, False)
        auth.login(strategy="interactive")
        self.assertEqual(auth.authenticated, True)
        self.assertEqual(auth.token, json_response)

        # test that we are creating a session with the proper headers
        session = auth.get_session()
        headers = session.headers
        self.assertTrue("User-Agent" in headers)
        self.assertTrue("earthaccess" in headers["User-Agent"])

    @responses.activate
    @mock.patch("getpass.getpass")
    @mock.patch("builtins.input")
    def test_auth_can_create_proper_credentials(self, user_input, user_password):
        user_input.return_value = "user"
        user_password.return_value = "password"
        json_response = {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"}

        responses.add(
            responses.POST,
            "https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
            json=json_response,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={},
            status=200,
        )

        # Test
        auth = Auth()
        auth.login(strategy="interactive")
        self.assertEqual(auth.authenticated, True)
        self.assertEqual(auth.password, "password")
        self.assertEqual(auth.token, json_response)

    @responses.activate
    @mock.patch.dict(os.environ, {"EARTHDATA_TOKEN": "ABCDEFGHIJKLMNOPQ"})
    def test_auth_can_parse_existing_user_token(self):
        json_response = {"access_token": os.environ["EARTHDATA_TOKEN"]}

        # Test
        auth = Auth()
        auth.login(strategy="environment")
        self.assertEqual(auth.authenticated, True)
        self.assertEqual(auth.token, json_response)

    @responses.activate
    @mock.patch("getpass.getpass")
    @mock.patch("builtins.input")
    def test_auth_fails_for_wrong_credentials(self, user_input, user_password):
        user_input.return_value = "bad_user"
        user_password.return_value = "bad_password"
        json_response = {"error": "wrong credentials"}

        responses.add(
            responses.POST,
            "https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
            json=json_response,
            status=401,
        )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json=json_response,
            status=401,
        )
        # Test
        auth = Auth()
        with pytest.raises(LoginAttemptFailure):
            auth.login(strategy="interactive")

        self.assertEqual(auth.authenticated, False)
