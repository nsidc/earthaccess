from unittest.mock import patch

import icechunk as ic
import pytest

# temporary jankyness until https://github.com/nsidc/earthaccess/pull/1154 is ready
from earthaccess.icechunk_opener import (
    S3IcechunkCredentials,
    credential_endpoint_mapping as endpoints,
    get_virtual_chunk_credentials,
)
from icechunk import AnyCredential, S3StaticCredentials


@pytest.fixture
def empty_config_icechunk(tmp_path):
    """Create an icechunk store in a temporary directory with empty config."""
    # Create storage in temp directory
    storage = ic.storage.local_filesystem_storage(
        str(tmp_path.joinpath("empty_config_icechunk"))
    )

    # Initialize with empty repository
    ic.Repository.create(storage=storage, config=None)

    return storage


@pytest.fixture
def no_vcontainers_icechunk(tmp_path):
    """Create an icechunk store in a temporary directory with missing virtual chunk containers."""
    # Create storage in temp directory
    storage = ic.storage.local_filesystem_storage(
        str(tmp_path.joinpath("no_vcontainers_icechunk"))
    )

    # Initialize with empty repository
    config = ic.RepositoryConfig.default()
    repo = ic.Repository.create(storage=storage, config=config)
    repo.save_config()

    return storage


@pytest.fixture
@patch("earthaccess.__auth__.get_s3_credentials")
def mixed_virtual_icechunk(mock_get_s3_credentials, tmp_path):
    """Create an icechunk store in a temporary directory with two different containers that can be authenticated."""
    mock_creds = {
        "accessKeyId": "ak",
        "secretAccessKey": "sk",
        "expiration": "2025-12-15T14:30:45.123456Z",
        "sessionToken": "my-token",
    }
    mock_get_s3_credentials.return_value = mock_creds

    storage = ic.storage.local_filesystem_storage(
        str(tmp_path.joinpath("mixed_virtual_icechunk_store"))
    )

    # Initialize with empty repository
    config = config = ic.RepositoryConfig.default()

    credentials_raw = {}
    # set virtual chunk containers and authenticate
    for bucket in ["podaac-ops-cumulus-protected", "gesdisc-cumulus-prod-protected"]:
        bucket_url = "s3://" + bucket + "/"

        # TODO: how can i make this not at all use the internet? (turn off the container verification)
        config.set_virtual_chunk_container(
            ic.VirtualChunkContainer(bucket_url, ic.s3_store(region="us-west-2"))
        )
        custom_creds = S3IcechunkCredentials(endpoints[bucket])
        credentials_raw[bucket_url] = ic.s3_refreshable_credentials(custom_creds)

    credentials = ic.containers_credentials(credentials_raw)
    ic.Repository.create(
        storage=storage, config=config, authorize_virtual_chunk_access=credentials
    )
    return storage


@pytest.fixture
@patch("earthaccess.__auth__.get_s3_credentials")
def partial_virtual_icechunk(mock_get_s3_credentials, tmp_path):
    """Create an icechunk store in a temporary directory where only one chunk containers can be authenticated."""
    mock_creds = {
        "accessKeyId": "ak",
        "secretAccessKey": "sk",
        "expiration": "2025-12-15T14:30:45.123456Z",
        "sessionToken": "my-token",
    }
    mock_get_s3_credentials.return_value = mock_creds

    # Create storage in temp directory
    storage = ic.storage.local_filesystem_storage(
        str(tmp_path.joinpath("partial_virtual_icechunk_store"))
    )

    # Initialize with empty repository
    config = config = ic.RepositoryConfig.default()

    # set virtual chunk containers and authenticate
    bucket = "podaac-ops-cumulus-protected"
    bucket_url = "s3://" + bucket + "/"

    # TODO: how can i make this not at all use the internet? (turn off the container verification)
    config.set_virtual_chunk_container(
        ic.VirtualChunkContainer(bucket_url, ic.s3_store(region="us-west-2"))
    )
    config.set_virtual_chunk_container(
        ic.VirtualChunkContainer(
            "s3://nasa-waterinsight/", ic.s3_store(region="us-west-2")
        )
    )

    custom_creds = S3IcechunkCredentials(endpoints[bucket])
    credentials = ic.containers_credentials(
        {
            bucket_url: ic.s3_refreshable_credentials(custom_creds),
            "s3://nasa-waterinsight/": ic.s3_anonymous_credentials(),
        }
    )
    ic.Repository.create(
        storage=storage, config=config, authorize_virtual_chunk_access=credentials
    )

    return storage


@pytest.fixture
@patch("earthaccess.__auth__.get_s3_credentials")
def full_virtual_icechunk(mock_get_s3_credentials, tmp_path):
    """Create an icechunk store in a temporary directory where the single chunk containers can be authenticated."""
    mock_creds = {
        "accessKeyId": "ak",
        "secretAccessKey": "sk",
        "expiration": "2025-12-15T14:30:45.123456Z",
        "sessionToken": "my-token",
    }
    mock_get_s3_credentials.return_value = mock_creds

    # Create storage in temp directory
    storage = ic.storage.local_filesystem_storage(
        str(tmp_path.joinpath("full_virtual_icechunk_store"))
    )

    # Initialize with empty repository
    config = ic.RepositoryConfig.default()

    # set virtual chunk containers and authenticate
    bucket = "podaac-ops-cumulus-protected"
    bucket_url = "s3://" + bucket + "/"
    config.set_virtual_chunk_container(
        ic.VirtualChunkContainer(bucket_url, ic.s3_store(region="us-west-2"))
    )
    custom_creds = S3IcechunkCredentials(endpoints[bucket])
    credentials = ic.containers_credentials(
        {bucket_url: ic.s3_refreshable_credentials(custom_creds)}
    )
    ic.Repository.create(
        storage=storage, config=config, authorize_virtual_chunk_access=credentials
    )
    return storage


class Test_S3IcechunkCredentials:
    @pytest.mark.parametrize("endpoint", ["a", "b"])
    def test_init(self, endpoint):
        creds_provider = S3IcechunkCredentials(endpoint=endpoint)
        creds_provider.endpoint = endpoint

    @patch("earthaccess.__auth__.get_s3_credentials")
    def test_no_creds(self, mock_get_s3_credentials):
        mock_get_s3_credentials.return_value = {}

        endpoint = "not.a-valid-enpoint.com"
        creds_provider = S3IcechunkCredentials(endpoint=endpoint)
        with pytest.raises(
            ValueError, match="Got no credentials from endpoint not.a-valid-enpoint.com"
        ):
            creds_provider()

    @patch("earthaccess.__auth__.get_s3_credentials")
    def test_get_valid_creds(self, mock_get_s3_credentials):
        mock_creds = {
            "accessKeyId": "ak",
            "secretAccessKey": "sk",
            "expiration": "2025-12-15T14:30:45.123456Z",
            "sessionToken": "my-token",
        }
        mock_get_s3_credentials.return_value = mock_creds

        endpoint = "https://archive.podaac.earthdata.nasa.gov/s3credentials"
        creds_provider = S3IcechunkCredentials(endpoint=endpoint)
        creds = creds_provider()
        assert isinstance(creds, S3StaticCredentials)


class Test_get_virtual_chunk_credentials:
    def test_get_virtual_chunk_credentials_empty(self, empty_config_icechunk):
        with pytest.warns(match="Got empty config"):
            get_virtual_chunk_credentials(storage=empty_config_icechunk)

    def test_get_virtual_chunk_credentials_no_containers(self, no_vcontainers_icechunk):
        with pytest.raises(ValueError, match="No virtual chunk containers found."):
            get_virtual_chunk_credentials(storage=no_vcontainers_icechunk)

    @patch("earthaccess.__auth__.get_s3_credentials")
    def test_get_partial_virtual_chunk_credentials(
        self, mock_get_s3_credentials, partial_virtual_icechunk
    ):
        # Make sure that only the endpoints that match get a return!
        def mock_credentials(url):
            if url == "https://archive.podaac.earthdata.nasa.gov/s3credentials":
                return {
                    "accessKeyId": "ak",
                    "secretAccessKey": "sk",
                    "expiration": "2010",
                    "sessionToken": "my-token",
                }
            else:
                return {}

        mock_get_s3_credentials.side_effect = mock_credentials

        with pytest.warns(match="Could not build virtual chunk credentials for"):
            creds = get_virtual_chunk_credentials(storage=partial_virtual_icechunk)
        assert len(creds) == 1
        assert list(creds.keys())[0] == "s3://podaac-ops-cumulus-protected/"
        assert all([isinstance(c, AnyCredential) for c in creds.values()])

    @patch("earthaccess.__auth__.get_s3_credentials")
    def test_get_mixed_virtual_chunk_credentials(
        self, mock_get_s3_credentials, mixed_virtual_icechunk
    ):
        # Make sure that only the endpoints that match get a return!
        def mock_credentials(url):
            if url in [
                "https://archive.podaac.earthdata.nasa.gov/s3credentials",
                "https://data.gesdisc.earthdata.nasa.gov/s3credentials",
            ]:
                return {
                    "accessKeyId": "ak",
                    "secretAccessKey": "sk",
                    "expiration": "2010",
                    "sessionToken": "my-token",
                }
            else:
                return {}

        mock_get_s3_credentials.side_effect = mock_credentials
        creds = get_virtual_chunk_credentials(storage=mixed_virtual_icechunk)
        assert len(creds) == 2
        assert set(creds.keys()) == set(
            [
                "s3://podaac-ops-cumulus-protected/",
                "s3://gesdisc-cumulus-prod-protected/",
            ]
        )
        assert all([isinstance(c, AnyCredential) for c in creds.values()])

    @patch("earthaccess.__auth__.get_s3_credentials")
    def test_get_full_virtual_chunk_credentials(
        self, mock_get_s3_credentials, full_virtual_icechunk
    ):
        # Make sure that only the endpoints that match get a return!
        def mock_credentials(url):
            if url == "https://archive.podaac.earthdata.nasa.gov/s3credentials":
                return {
                    "accessKeyId": "ak",
                    "secretAccessKey": "sk",
                    "expiration": "2010",
                    "sessionToken": "my-token",
                }
            else:
                return {}

        mock_get_s3_credentials.side_effect = mock_credentials
        creds = get_virtual_chunk_credentials(storage=full_virtual_icechunk)
        assert len(creds) == 1
        assert list(creds.keys())[0] == "s3://podaac-ops-cumulus-protected/"
        assert all([isinstance(c, AnyCredential) for c in creds.values()])
