# package imports
import os
import unittest

import fsspec
import responses
from earthdata import Auth, Store


class TestStoreSessions(unittest.TestCase):
    @responses.activate
    def setUp(self):
        os.environ["EDL_USERNAME"] = "user"
        os.environ["EDL_PASSWORD"] = "password"
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

        self.auth = Auth().login(strategy="environment")
        self.assertEqual(self.auth.authenticated, True)
        self.assertTrue(self.auth.token in json_response)

    def tearDown(self):
        self.auth = None

    def test_store_can_create_https_fsspec_session(self):
        store = Store(self.auth)
        self.assertTrue(isinstance(store.auth, Auth))
        https_fs = store.get_https_session()
        self.assertEqual(type(https_fs), type(fsspec.filesystem("https")))
        return None

    @responses.activate
    def test_store_can_create_s3_fsspec_session(self):
        responses.add(
            responses.GET,
            "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
            json={
                "accessKeyId": "sure",
                "secretAccessKey": "correct",
                "sessionToken": "whynot",
            },
            status=200,
        )
        store = Store(self.auth)
        self.assertTrue(isinstance(store.auth, Auth))
        s3_fs = store.get_s3fs_session(daac="NSIDC")
        self.assertEqual(type(s3_fs), type(fsspec.filesystem("s3")))
        return None
