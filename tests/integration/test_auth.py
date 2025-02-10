import logging

import earthaccess
import earthaccess.daac
import pytest
import requests
import s3fs
from earthaccess.exceptions import LoginStrategyUnavailable

logger = logging.getLogger(__name__)


def test_auth_can_read_earthdata_env_variables():
    auth = earthaccess.login(strategy="environment")
    logger.info(f"Current username: {auth.username}")
    logger.info(f"earthaccess version: {earthaccess.__version__}")

    assert isinstance(auth, earthaccess.Auth)
    assert isinstance(earthaccess.__auth__, earthaccess.Auth)
    assert earthaccess.__auth__.authenticated


def test_auth_can_read_from_netrc_file(mock_netrc):
    auth = earthaccess.login(strategy="netrc")
    assert auth.authenticated


def test_auth_strategy_unavailable_netrc_is_not_present(mock_missing_netrc):
    with pytest.raises(LoginStrategyUnavailable):
        earthaccess.login(strategy="netrc")


def test_auth_populates_attrs():
    auth = earthaccess.login(strategy="environment")
    assert isinstance(auth, earthaccess.Auth)
    assert isinstance(earthaccess.__auth__, earthaccess.Auth)
    assert earthaccess.__auth__.authenticated


def test_auth_can_create_authenticated_requests_sessions():
    session = earthaccess.get_requests_https_session()
    assert "Authorization" in session.headers
    assert "Bearer" in session.headers["Authorization"]  # type: ignore


@pytest.mark.parametrize(
    "daac", [daac for daac in earthaccess.daac.DAACS if daac["s3-credentials"]]
)
def test_auth_can_fetch_s3_credentials(daac):
    auth = earthaccess.login(strategy="environment")
    assert auth.authenticated

    try:
        credentials = earthaccess.get_s3_credentials(daac["short-name"])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch S3 credentials: {e}")
    else:
        assert isinstance(credentials, dict)
        assert "accessKeyId" in credentials


@pytest.mark.parametrize("location", ({"daac": "podaac"}, {"provider": "pocloud"}))
def test_get_s3_credentials_lowercase_location(location):
    earthaccess.login(strategy="environment")
    creds = earthaccess.get_s3_credentials(**location)

    assert creds
    assert all(
        creds[key]
        for key in ["accessKeyId", "secretAccessKey", "sessionToken", "expiration"]
    )


@pytest.mark.parametrize("location", ({"daac": "podaac"}, {"provider": "pocloud"}))
def test_get_s3_filesystem_lowercase_location(location):
    earthaccess.login(strategy="environment")
    fs = earthaccess.get_s3_filesystem(**location)

    assert isinstance(fs, s3fs.S3FileSystem)
    assert all(fs.storage_options[key] for key in ["key", "secret", "token"])
