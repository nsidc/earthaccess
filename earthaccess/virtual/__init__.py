"""Virtual dataset utilities for cloud-native access to NASA Earthdata granules.

This subpackage provides tools for creating virtual xarray Datasets from
NASA Earthdata granules without downloading data, using VirtualiZarr parsers,
and for opening existing virtual stores (Icechunk / kerchunk references).

Public API
----------
- ``virtualize`` — create a virtual (or loaded) xarray Dataset from granules.
- ``open_virtual`` — open an existing virtual store (Icechunk, kerchunk .parquet
  or .json references) from a URI.
- ``homogenize_dataset_codec_level`` — patch Zlib codec levels on all
  ``ManifestArray`` objects in a virtual dataset (power-users).
- ``SUPPORTED_PARSERS`` — frozenset of recognised parser name strings.
- ``get_granule_credentials_endpoint_and_region`` — resolve S3 credentials
  for a granule (useful for advanced direct-access workflows).

Requires the ``earthaccess[virtualizarr]`` optional extra.
"""

from __future__ import annotations

from earthaccess.virtual._credentials import (
    get_granule_credentials_endpoint_and_region,
)
from earthaccess.virtual._parser import (
    SUPPORTED_PARSERS,
    homogenize_dataset_codec_level,
)
from earthaccess.virtual.core import open_virtual, virtualize

__all__ = [
    "SUPPORTED_PARSERS",
    "get_granule_credentials_endpoint_and_region",
    "homogenize_dataset_codec_level",
    "open_virtual",
    "virtualize",
]
