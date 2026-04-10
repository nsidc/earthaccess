"""Credential resolution and obstore registry construction.

Provides two public helpers:

- ``get_granule_credentials_endpoint_and_region`` – resolve the NASA S3
  credentials endpoint for a granule, falling back to a CMR collection query.
- ``build_obstore_registry`` – build an ``ObjectStoreRegistry`` suitable for
  passing to ``vz.open_virtual_mfdataset``.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import earthaccess
from earthaccess.virtual._types import AccessType

if TYPE_CHECKING:
    from virtualizarr.registry import ObjectStoreRegistry

logger = logging.getLogger(__name__)


def get_granule_credentials_endpoint_and_region(
    granule: earthaccess.DataGranule,
) -> tuple[str, str]:
    """Return the S3 credentials endpoint and region for a granule.

    The endpoint is read from the granule's UMM-G record first.  If absent, a
    CMR collection query is performed and the information is taken from the
    UMM-C record.

    Parameters:
        granule: A single ``DataGranule`` object.

    Returns:
        A tuple of ``(credentials_endpoint, region)``.  ``region`` defaults to
        ``"us-west-2"`` when not present in the collection record.

    Raises:
        ValueError: If no ``S3CredentialsAPIEndpoint`` can be resolved from
            either the granule or its parent collection.
    """
    credentials_endpoint = granule.get_s3_credentials_endpoint()
    region = "us-west-2"

    if credentials_endpoint is None:
        collection_results = earthaccess.search_datasets(
            count=1,
            concept_id=granule["meta"]["collection-concept-id"],
        )
        collection_s3_bucket = collection_results[0].s3_bucket()
        credentials_endpoint = collection_s3_bucket.get("S3CredentialsAPIEndpoint")
        region = collection_s3_bucket.get("Region", "us-west-2")

    if credentials_endpoint is None:
        raise ValueError(
            "The collection did not provide an S3CredentialsAPIEndpoint. "
            "Direct S3 access is not available for this granule.",
        )

    return credentials_endpoint, region


def validate_granules(
    granules: Sequence[earthaccess.DataGranule],
) -> None:
    """Validate that the given granules are suitable for virtualizing.
    Parameters:
        granules: The granules to validate.

    Raises:
        ValueError: If the list of granules is empty.
        ValueError: If any granule does not have data links.
    """
    if not granules or len(granules) == 0:
        raise ValueError("No valid granules provided.")
    for granule in granules:
        if not granule.data_links():
            raise ValueError(
                f"Granule {granule['meta']['concept-id']} has no data links.",
            )


def build_obstore_registry(
    granules: Sequence[earthaccess.DataGranule],
    access: AccessType,
) -> ObjectStoreRegistry:
    """Build an obstore ``ObjectStoreRegistry`` for the given granules.

    Parameters:
        granules: The granules to build the registry for.  Only the first
            granule is inspected to determine the host/bucket.
        access: ``"direct"`` builds an authenticated ``S3Store``; ``"indirect"``
            builds an ``HTTPStore`` using the user's EDL Bearer token.

    Returns:
        A configured ``ObjectStoreRegistry``.

    Raises:
        ValueError: If ``access="indirect"`` and the user is not authenticated.
        ValueError: If ``access="direct"`` and no S3 credentials endpoint can
            be resolved.
        ImportError: If ``earthaccess[virtualizarr]`` is not installed.
    """
    try:
        from obstore.auth.earthdata import NasaEarthdataCredentialProvider
        from obstore.store import HTTPStore, S3Store
        from virtualizarr.registry import ObjectStoreRegistry
    except ImportError:
        raise ImportError(
            "earthaccess.virtualize() requires `pip install earthaccess[virtualizarr]`",
        ) from None

    validate_granules(granules)

    parsed_url = urlparse(granules[0].data_links(access=access)[0])
    auth = earthaccess.__auth__
    edl_token = getattr(auth, "token", None)
    if not edl_token or "access_token" not in edl_token:
        raise ValueError(
            "You must be logged in to use indirect access. "
            "Call earthaccess.login() first.",
        )
    token: str = edl_token["access_token"]

    if access == "direct":
        credentials_endpoint, region = get_granule_credentials_endpoint_and_region(
            granules[0],
        )
        bucket = parsed_url.netloc
        s3_store = S3Store(
            bucket=bucket,
            region=region,
            credential_provider=NasaEarthdataCredentialProvider(
                credentials_endpoint, auth=token,
            ),
            virtual_hosted_style_request=False,
            client_options={"allow_http": True},
        )
        return ObjectStoreRegistry({f"s3://{bucket}": s3_store})

    # indirect — HTTPS
    domain = parsed_url.netloc
    http_store = HTTPStore.from_url(
        f"https://{domain}",
        client_options={
            "default_headers": {
                "Authorization": f"Bearer {token}",
            },
        },
    )
    return ObjectStoreRegistry({f"https://{domain}": http_store})
