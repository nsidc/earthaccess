# package imports
import os
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import fsspec
import pytest
import responses
import s3fs
from earthaccess import Auth, Store
from earthaccess.auth import SessionWithHeaderRedirection
from earthaccess.exceptions import DownloadFailure, EulaNotAccepted
from earthaccess.store import EarthAccessFile, _open_files
from pqdm.threads import pqdm


class TestEula(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "EARTHDATA_USERNAME": "user_no_eula",
            "EARTHDATA_PASSWORD": "password",
        },
        clear=True,
    )
    @responses.activate
    def setUp(self):
        json_response = {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"}
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json=json_response,
            status=200,
        )
        responses.add(
            responses.POST,
            "https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
            json=json_response,
            status=200,
        )

        self.auth = Auth()
        self.auth.login(strategy="environment")
        assert self.auth.authenticated

    @responses.activate
    def test_eula_detects_401_errors(self):
        response = " blah blah Eula bing!"
        mocked_url = "https://example.com/protected_file.nc"
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            url=mocked_url,
            body=response,
            status=401,
        )
        store = Store(self.auth)
        with self.assertRaisesRegex(
            EulaNotAccepted, f"Eula Acceptance Failure for {mocked_url}"
        ):
            store.get([mocked_url], "/tmp")

    @responses.activate
    def test_detects_non_eula_errors(self):
        response = " blah blah error!"
        mocked_url = "https://example.com/protected_file.nc"
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={},
            status=200,
        )
        responses.add(
            responses.GET,
            url=mocked_url,
            body=response,
            status=401,
        )
        store = Store(self.auth)
        with self.assertRaisesRegex(
            DownloadFailure, f"Download failed for {mocked_url}. Status code: 401"
        ):
            store.get([mocked_url], "/tmp")

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
        assert isinstance(store.auth, Auth)
        https_fs = store.get_fsspec_session()
        assert type(https_fs) is type(fsspec.filesystem("https"))
        return None


class TestStoreSessions(unittest.TestCase):
    @responses.activate
    @patch.dict(
        os.environ,
        {
            "EARTHDATA_USERNAME": "user",
            "EARTHDATA_PASSWORD": "password",
        },
        clear=True,
    )
    def setUp(self):
        json_response = {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"}
        responses.add(
            responses.POST,
            "https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
            json=json_response,
            status=200,
        )
        self.auth = Auth()
        self.auth.login(strategy="environment")
        self.assertEqual(self.auth.authenticated, True)
        self.assertEqual(self.auth.token, json_response)

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

    @responses.activate
    def test_session_reuses_token_download(self):
        mock_creds = {
            "accessKeyId": "sure",
            "secretAccessKey": "correct",
            "sessionToken": "whynot",
        }
        test_cases = [
            (2, 500),  # 2 threads, 500 files
            (4, 400),  # 4 threads, 400 files
            (8, 5000),  # 8 threads, 5k files
        ]
        for n_threads, n_files in test_cases:
            with self.subTest(n_threads=n_threads, n_files=n_files):
                urls = [f"https://example.com/file{i}" for i in range(1, n_files + 1)]
                for i, url in enumerate(urls):
                    responses.add(
                        responses.GET, url, body=f"Content of file {i + 1}", status=200
                    )

                edl_hostname = "urs.earthdata.nasa.gov"
                mock_auth = MagicMock()
                mock_auth.authenticated = True
                mock_auth.system.edl_hostname = edl_hostname
                responses.add(
                    responses.GET,
                    "https://urs.earthdata.nasa.gov/profile",
                    json=mock_creds,
                    status=200,
                )

                original_session = SessionWithHeaderRedirection(edl_hostname)
                original_session.cookies.set("sessionid", "mocked-session-cookie")
                mock_auth.get_session.return_value = original_session

                store = Store(auth=mock_auth)
                store.thread_locals = threading.local()  # Use real thread-local storage

                # Track cloned sessions
                cloned_sessions = set()

                def mock_clone_session_in_local_thread(original_session):
                    """Mock session cloning to track cloned sessions."""
                    if not hasattr(store.thread_locals, "local_thread_session"):
                        session = SessionWithHeaderRedirection(edl_hostname)
                        session.cookies.update(original_session.cookies)
                        cloned_sessions.add(id(session))
                        store.thread_locals.local_thread_session = session

                with patch.object(
                    store,
                    "_clone_session_in_local_thread",
                    side_effect=mock_clone_session_in_local_thread,
                ):
                    mock_directory = Path("/mock/directory")
                    downloaded_files = []

                    def mock_download_file(url):
                        """Mock file download to track downloaded files."""
                        # Ensure session cloning happens before downloading
                        store._clone_session_in_local_thread(original_session)
                        downloaded_files.append(url)
                        return mock_directory / f"{url.split('/')[-1]}"

                    with patch.object(
                        store, "_download_file", side_effect=mock_download_file
                    ):
                        # Test multi-threaded download
                        pqdm(urls, store._download_file, n_jobs=n_threads)  # type: ignore

                # We make sure we reuse the token up to N threads
                self.assertTrue(len(cloned_sessions) <= n_threads)

                self.assertEqual(len(downloaded_files), n_files)  # 10 files downloaded
                self.assertCountEqual(downloaded_files, urls)  # All files accounted for


def test_earthaccess_file_getattr():
    fs = fsspec.filesystem("memory")
    with fs.open("foo", "wb") as f:
        earthaccess_file = EarthAccessFile(f, granule="foo")
        assert f.tell == earthaccess_file.tell
    fs.store.clear()


@pytest.mark.parametrize(
    "file_size, open_kwargs, expected_cache_type, expected_block_size",
    [
        # Case 1: Small file, defaults used
        (50 * 1024 * 1024, {}, "background", 4 * 1024 * 1024),
        # Case 2: Medium file, block_size scales up
        (300 * 1024 * 1024, {}, "background", 8 * 1024 * 1024),
        # Case 3: Large file, hits max block size
        (1600 * 1024 * 1024, {}, "background", 16 * 1024 * 1024),
        # Case 4: Override cache_type and block_size
        (
            600 * 1024 * 1024,
            {"cache_type": "readahead", "block_size": 1024},
            "readahead",
            1024,
        ),
        # Case 5: Override only one (block_size)
        (
            600 * 1024 * 1024,
            {"block_size": 8 * 1024 * 1024},
            "background",
            8 * 1024 * 1024,
        ),
    ],
)
def test_open_files_parametrized(
    file_size, open_kwargs, expected_cache_type, expected_block_size
):
    fs = MagicMock()
    fs.info.return_value = {"size": file_size}
    fs.open = MagicMock()

    url = "https://example.com/file.nc"
    granule = MagicMock()
    url_mapping = {url: granule}

    result = _open_files(url_mapping, fs, open_kwargs=open_kwargs)

    fs.open.assert_called_once()
    args, kwargs = fs.open.call_args

    assert args[0] == url
    assert result[0] is not None
    assert kwargs["cache_type"] == expected_cache_type
    assert kwargs["block_size"] == expected_block_size or (
        isinstance(expected_block_size, float)
        and abs(kwargs["block_size"] - expected_block_size) < 1e5
    )
