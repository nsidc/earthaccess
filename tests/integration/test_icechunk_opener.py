import pytest
from earthaccess.icechunk_opener import get_virtual_chunk_credentials, open_icechunk_from_url

import icechunk

def test_mixed_case_mur():
    """store is on public bucket, but data in EDL buckets"""
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
    """store and native chunks on EDL bucket"""
    # waiting for test datasets on PODAAC
    # open
    pass

def test_full_edl_store():
    """store and virtual chunks on EDL bucket"""
    # waiting for test datasets on PODAAC
    pass
