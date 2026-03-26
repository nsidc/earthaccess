"""Unit tests for earthaccess.virtual._credentials.

TDD-first: tests are written before the implementation.

These tests mock all external I/O (obstore, NASA auth endpoints).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_granule(
    url: str = "s3://bucket/path/file.nc",
    provider_id: str = "PODAAC",
    collection_concept_id: str = "C1234-PODAAC",
    s3_endpoint: str | None = "https://data.earthdata.nasa.gov/s3credentials",
) -> MagicMock:
    g = MagicMock()
    g.data_links.return_value = [url]
    g.get_s3_credentials_endpoint.return_value = s3_endpoint
    g.__getitem__ = MagicMock(
        side_effect=lambda key: {
            "meta": {
                "provider-id": provider_id,
                "collection-concept-id": collection_concept_id,
            }
        }[key]
    )
    return g


# ---------------------------------------------------------------------------
# get_granule_credentials_endpoint_and_region
# ---------------------------------------------------------------------------


def test_returns_endpoint_and_region_from_granule_umm() -> None:
    """Returns (endpoint, region) directly from the granule UMM-G record."""
    from earthaccess.virtual._credentials import (
        get_granule_credentials_endpoint_and_region,
    )

    granule = _make_granule(s3_endpoint="https://data.earthdata.nasa.gov/s3creds")
    endpoint, region = get_granule_credentials_endpoint_and_region(granule)
    assert endpoint == "https://data.earthdata.nasa.gov/s3creds"
    assert region == "us-west-2"


def test_falls_back_to_collection_query_when_granule_has_no_endpoint() -> None:
    """Falls back to a CMR collection query when UMM-G has no endpoint."""
    from earthaccess.virtual._credentials import (
        get_granule_credentials_endpoint_and_region,
    )

    granule = _make_granule(s3_endpoint=None)

    mock_collection = MagicMock()
    mock_collection.s3_bucket.return_value = {
        "S3CredentialsAPIEndpoint": "https://fallback.nasa.gov/s3creds",
        "Region": "us-east-1",
    }

    with patch(
        "earthaccess.virtual._credentials.earthaccess.search_datasets",
        return_value=[mock_collection],
    ):
        endpoint, region = get_granule_credentials_endpoint_and_region(granule)

    assert endpoint == "https://fallback.nasa.gov/s3creds"
    assert region == "us-east-1"


def test_fallback_region_defaults_to_us_west_2_when_not_in_collection() -> None:
    """Region defaults to us-west-2 when not present in the collection record."""
    from earthaccess.virtual._credentials import (
        get_granule_credentials_endpoint_and_region,
    )

    granule = _make_granule(s3_endpoint=None)

    mock_collection = MagicMock()
    mock_collection.s3_bucket.return_value = {
        "S3CredentialsAPIEndpoint": "https://fallback.nasa.gov/s3creds",
        # Region intentionally absent
    }

    with patch(
        "earthaccess.virtual._credentials.earthaccess.search_datasets",
        return_value=[mock_collection],
    ):
        endpoint, region = get_granule_credentials_endpoint_and_region(granule)

    assert region == "us-west-2"


def test_raises_value_error_when_endpoint_not_resolvable() -> None:
    """Raises ValueError if neither UMM-G nor the collection has an endpoint."""
    from earthaccess.virtual._credentials import (
        get_granule_credentials_endpoint_and_region,
    )

    granule = _make_granule(s3_endpoint=None)

    mock_collection = MagicMock()
    mock_collection.s3_bucket.return_value = {}  # no endpoint key

    with patch(
        "earthaccess.virtual._credentials.earthaccess.search_datasets",
        return_value=[mock_collection],
    ):
        with pytest.raises(ValueError, match="S3CredentialsAPIEndpoint"):
            get_granule_credentials_endpoint_and_region(granule)


# ---------------------------------------------------------------------------
# build_obstore_registry – indirect (HTTPS) access
# ---------------------------------------------------------------------------


def test_build_registry_indirect_returns_registry() -> None:
    """build_obstore_registry with indirect access returns an ObjectStoreRegistry."""
    from earthaccess.virtual._credentials import build_obstore_registry

    granule = _make_granule(url="https://data.nasa.gov/path/file.nc")

    mock_auth = MagicMock()
    mock_auth.token = {"access_token": "tok123"}

    with patch("earthaccess.virtual._credentials.earthaccess") as mock_ea:
        mock_ea.__auth__ = mock_auth
        registry = build_obstore_registry([granule], access="indirect")

    assert registry is not None


def test_build_registry_indirect_raises_when_not_authenticated() -> None:
    """build_obstore_registry raises ValueError when user is not logged in."""
    from earthaccess.virtual._credentials import build_obstore_registry

    granule = _make_granule(url="https://data.nasa.gov/path/file.nc")

    mock_auth = MagicMock()
    mock_auth.token = None  # not authenticated

    with patch("earthaccess.virtual._credentials.earthaccess") as mock_ea:
        mock_ea.__auth__ = mock_auth
        with pytest.raises(ValueError, match="[Ll]ogged in|authenticated|token"):
            build_obstore_registry([granule], access="indirect")


# ---------------------------------------------------------------------------
# build_obstore_registry – direct (S3) access
# ---------------------------------------------------------------------------


def test_build_registry_direct_returns_registry() -> None:
    """build_obstore_registry with direct access returns an ObjectStoreRegistry."""
    from earthaccess.virtual._credentials import build_obstore_registry

    granule = _make_granule(url="s3://bucket/file.nc")

    with patch(
        "earthaccess.virtual._credentials.get_granule_credentials_endpoint_and_region",
        return_value=("https://creds.nasa.gov/s3creds", "us-west-2"),
    ):
        registry = build_obstore_registry([granule], access="direct")

    assert registry is not None
