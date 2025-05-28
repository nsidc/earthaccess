# package imports
import logging
import os
import unittest
from contextlib import contextmanager
from unittest import mock

import earthaccess
import pytest
import responses
from earthaccess import Auth
from earthaccess.exceptions import LoginAttemptFailure

logger = logging.getLogger(__name__)

@contextmanager
def tmp_env(overrides):
    original = os.environ.copy()
    os.environ.update(overrides)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)



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
        session = auth.get_session()
        headers = session.headers
        self.assertEqual(auth.authenticated, False)
        auth.login(strategy="interactive")
        self.assertEqual(auth.authenticated, True)
        self.assertEqual(auth.token, json_response)

        # test that we are creating a session with the proper headers
        self.assertTrue("User-Agent" in headers)
        self.assertTrue("earthaccess" in headers["User-Agent"])

    @responses.activate
    def test_auth_token_only_workflow(self):

        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={"email_address": "test@test.edu"},
            status=200,
        )

        token = "my_secret_token"

        with tmp_env({"EARTHDATA_TOKEN": token}):
            assert os.environ["EARTHDATA_TOKEN"] == token
            auth = Auth()
            self.assertEqual(auth.authenticated, False)
            auth.login(strategy="token")

            session = auth.get_session()
            headers = session.headers
            self.assertEqual(auth.authenticated, True)
            self.assertTrue(token in headers["Authorization"])
            self.assertTrue("earthaccess" in headers["User-Agent"])
            self.assertTrue(len(responses.calls) == 0)

        auth = Auth()

        auth.login(strategy="token", token=token)
        session = auth.get_session()
        headers = session.headers
        self.assertEqual(auth.authenticated, True)
        self.assertTrue(token in headers["Authorization"])
        self.assertTrue("earthaccess" in headers["User-Agent"])
        self.assertTrue(len(responses.calls) == 0)

        # Top level API

        with tmp_env({"EARTHDATA_TOKEN": token}):
            auth = earthaccess.login()
            self.assertTrue(auth.authenticated)
            session = auth.get_session()
            headers = session.headers
            self.assertEqual(auth.authenticated, True)
            self.assertTrue(token in headers["Authorization"])
            self.assertTrue("earthaccess" in headers["User-Agent"])
            self.assertTrue(len(responses.calls) >= 0) # TODO: make this 0 calls in Store()


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
