import icechunk
from earthaccess.icechunk import (
    get_virtual_chunk_credentials,
    open_icechunk_from_url
)
import pytest

@pytest.mark.xfail
def test_full_edl_store():
    #TODO set up an actual test case here
    url = 'somethign'
    store = open_icechunk_from_url(url)


def test_mixed_case_mur():
    storage = icechunk.s3_storage(
        bucket = 'nasa-eodc-public',
        prefix = 'icechunk/MUR-JPL-L4-GLOB-v4.1-virtual-v2-p2',
        anonymous=True,
    )
    vchunk_credentials = get_virtual_chunk_credentials(storage)
    icechunk.Repository.open(
        storage=storage, 
        authorize_virtual_chunk_access=vchunk_credentials
    )

