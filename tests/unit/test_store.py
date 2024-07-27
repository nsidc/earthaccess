# package imports
import os
import unittest

import fsspec
import pytest
import responses
import s3fs
from earthaccess import Auth, Store


class TestStoreSessions(unittest.TestCase):
    @responses.activate
    def setUp(self):
        os.environ["EARTHDATA_USERNAME"] = "user"
        os.environ["EARTHDATA_PASSWORD"] = "password"
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
        self.auth = Auth()
        self.auth.login(strategy="environment")
        self.assertEqual(self.auth.authenticated, True)
        self.assertTrue(self.auth.token in json_response)

    def tearDown(self):
        self.auth = None

    @responses.activate
    def test_store_can_create_https_fsspec_session(self):
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={},
            status=200,
        )
        store = Store(self.auth)
        self.assertTrue(isinstance(store.auth, Auth))
        https_fs = store.get_fsspec_session()
        self.assertEqual(type(https_fs), type(fsspec.filesystem("https")))
        return None

    @responses.activate
    def test_store_can_create_s3_fsspec_session(self):
        from earthaccess.daac import DAACS

        custom_endpoints = [
            "https://archive.swot.podaac.earthdata.nasa.gov/s3credentials",
            "https://api.giovanni.earthdata.nasa.gov/s3credentials",
            "https://data.laadsdaac.earthdatacloud.nasa.gov/s3credentials",
        ]
        mock_creds = {
            "accessKeyId": "sure",
            "secretAccessKey": "correct",
            "sessionToken": "whynot",
        }
        expected_storage_options = {
            "key": mock_creds["accessKeyId"],
            "secret": mock_creds["secretAccessKey"],
            "token": mock_creds["sessionToken"],
        }

        for endpoint in custom_endpoints:
            responses.add(
                responses.GET,
                endpoint,
                json=mock_creds,
                status=200,
            )

        for daac in DAACS:
            if "s3-credentials" in daac:
                responses.add(
                    responses.GET,
                    daac["s3-credentials"],
                    json=mock_creds,
                    status=200,
                )
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json=mock_creds,
            status=200,
        )

        store = Store(self.auth)
        self.assertTrue(isinstance(store.auth, Auth))
        for daac in [
            "NSIDC",
            "PODAAC",
            "LPDAAC",
            "ORNLDAAC",
            "GES_DISC",
            "ASF",
            "OBDAAC",
            "ASDC",
        ]:
            s3_fs = store.get_s3_filesystem(daac=daac)
            assert isinstance(s3_fs, s3fs.S3FileSystem)
            assert s3_fs.storage_options == expected_storage_options

        for endpoint in custom_endpoints:
            s3_fs = store.get_s3_filesystem(endpoint=endpoint)
            assert isinstance(s3_fs, s3fs.S3FileSystem)
            assert s3_fs.storage_options == expected_storage_options

        for provider in [
            "NSIDC_CPRD",
            "POCLOUD",
            "LPCLOUD",
            "ORNL_CLOUD",
            "GES_DISC",
            "ASF",
            "OB_CLOUD",
            "LARC_CLOUD",
        ]:
            s3_fs = store.get_s3_filesystem(provider=provider)
            assert isinstance(s3_fs, s3fs.S3FileSystem)
            assert s3_fs.storage_options == expected_storage_options

        # Ensure informative error is raised
        with pytest.raises(ValueError, match="parameters must be specified"):
            store.get_s3_filesystem()

        return None
