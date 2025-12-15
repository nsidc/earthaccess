import icechunk as ic
import pytest

# temporary jankyness until https://github.com/nsidc/earthaccess/pull/1154 is ready
from earthaccess.icechunk_opener import (
    S3IcechunkCredentials,
    credential_endpoint_mapping as endpoints,
    get_virtual_chunk_credentials,
)
from icechunk import S3StaticCredentials


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


# @pytest.fixture
# def partial_virtual_icechunk(tmp_path):
#     """Create an icechunk store in a temporary directory where only some of the chunk containers can be authenticated"""


#     # Create storage in temp directory
#     storage = ic.storage.local_filesystem_storage(str(tmp_path.joinpath("icechunk_store")))

#     # Initialize with empty repository
#     config = config = ic.RepositoryConfig.default()
#     ic.Repository.create(storage=storage, config=config)

#     # set virtual chunk containers

#     return storage


@pytest.fixture
def partial_virtual_icechunk(tmp_path):
    """Create an icechunk store in a temporary directory where all chunk containers can be authenticated."""
    # Create storage in temp directory
    storage = ic.storage.local_filesystem_storage(
        str(tmp_path.joinpath("icechunk_store"))
    )

    # Initialize with empty repository
    config = config = ic.RepositoryConfig.default()

    # set virtual chunk containers and authenticate
    bucket = "podaac-ops-cumulus-protected"
    bucket_url = "s3://" + bucket + "/"
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
def full_virtual_icechunk(tmp_path):
    """Create an icechunk store in a temporary directory where all chunk containers can be authenticated."""
    # Create storage in temp directory
    storage = ic.storage.local_filesystem_storage(
        str(tmp_path.joinpath("icechunk_store"))
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
    def test_no_creds(self):
        endpoint = "not.a-valid-enpoint.com"
        creds_provider = S3IcechunkCredentials(endpoint=endpoint)
        with pytest.raises(
            ValueError, match="Got no credentials from endpoint not.a-valid-enpoint.com"
        ):
            creds_provider()

    def test_get_valid_creds(self):
        endpoint = "https://archive.podaac.earthdata.nasa.gov/s3credentials"
        creds_provider = S3IcechunkCredentials(endpoint=endpoint)
        creds = creds_provider()
        assert isinstance(creds, S3StaticCredentials)


class Test_get_virtual_chunk_credentials:
    def test_get_virtual_chunk_credentials_empty(self, empty_config_icechunk):
        with pytest.raises(ValueError, match="Got empty config"):
            get_virtual_chunk_credentials(storage=empty_config_icechunk)

    def test_get_virtual_chunk_credentials_no_containers(self, no_vcontainers_icechunk):
        with pytest.raises(ValueError, match="No virtual chunk containers found."):
            get_virtual_chunk_credentials(storage=no_vcontainers_icechunk)

    # these following tests are not entirely unit tests I guess since they depend on the actual
    def test_get_partial_virtual_chunk_credentials(self, partial_virtual_icechunk):
        with pytest.warns(match="Could not build virtual chunk credentials for"):
            creds = get_virtual_chunk_credentials(storage=partial_virtual_icechunk)
        assert len(creds) == 1
        assert list(creds.keys())[0] == "s3://podaac-ops-cumulus-protected/"
        # TODO: how can I assert that the values are an icechunk creds type...

    def test_get_virtual_chunk_credentials(self, full_virtual_icechunk):
        creds = get_virtual_chunk_credentials(storage=full_virtual_icechunk)
        assert len(creds) == 1
        assert list(creds.keys())[0] == "s3://podaac-ops-cumulus-protected/"
        # TODO: how can I assert that the values are an icechunk creds type...
