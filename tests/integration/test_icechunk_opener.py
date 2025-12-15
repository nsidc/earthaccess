import icechunk
from earthaccess.icechunk_opener import (
    get_virtual_chunk_credentials,
    open_icechunk_from_url,
)


def test_mixed_case_mur():
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


def test_native_edl_store():
    """Store and native chunks on EDL bucket."""
    open_icechunk_from_url(
        "s3://podaac-ops-cumulus-public/virtual_collections/earthaccess_integration_testing/icechunk_native/"
    )


def test_full_edl_store():
    """Store and virtual chunks on EDL bucket."""
    # waiting for test datasets on PODAAC
    pass
