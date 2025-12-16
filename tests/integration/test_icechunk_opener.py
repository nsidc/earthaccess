import icechunk
import pytest
from earthaccess.icechunk_opener import (
    get_virtual_chunk_credentials,
    open_icechunk_from_url,
    S3IcechunkCredentials
)
from icechunk import S3StaticCredentials
from icechunk.store import IcechunkStore

import earthaccess
#TODO: I this the way to do it?
earthaccess.login()

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


class Test_RealWorldExamples:
    def test_mur_credentials_only(self):
        """Store is on public bucket, but data in EDL buckets."""
        storage = icechunk.s3_storage(
            bucket="nasa-eodc-public",
            prefix="icechunk/MUR-JPL-L4-GLOB-v4.1-virtual-v2-p2",
            anonymous=True,
        )
        vchunk_credentials = get_virtual_chunk_credentials(storage)
        icechunk.Repository.open(
            storage=storage, authorize_virtual_chunk_access=vchunk_credentials
        )
        
    def test_native_edl_store(self):
        """Store and native chunks on EDL bucket."""
        #TODO: This store does not have the config persisted. If we get a chance for an update we should produce two native stores
        # One with and one without persisted config.
        with pytest.warns():
            store = open_icechunk_from_url(
                "s3://podaac-ops-cumulus-public/virtual_collections/earthaccess_integration_testing/icechunk_native/"
            )
            assert isinstance(store, IcechunkStore)

    def test_full_edl_store(self):
        """Store and virtual chunks on EDL bucket."""
        store = open_icechunk_from_url(
                "s3://podaac-ops-cumulus-public/virtual_collections/earthaccess_integration_testing/icechunk_virtual/"
            )
        assert isinstance(store, IcechunkStore)
        