
from earthaccess.icechunk import _get_credential_endpoint
import pytest

@pytest.mark.parametrize("url", ["s3://ghrcwuat-protected/sub/prefix", "s3://ghrcwuat-protected/sub/prefix/", "s3://ghrcwuat-protected", "s3://ghrcwuat-protected/"])
def test_get_credential_endpoint(url):
    assert _get_credential_endpoint(url) == "https://data.ghrc.uat.earthdata.nasa.gov/s3credentials"

def test_get_credential_endpoint_wrong_protocol():
    url = "gcs://ghrcwuat-protected"
    with pytest.raises(ValueError, match='Only s3 is supported'):
        _get_credential_endpoint(url)

def test_get_credential_endpoint_no_match():
    url = 's3://unknown-bucket'
    with pytest.raises(ValueError, match='Could not find any'):
        _get_credential_endpoint(url)