"""Virtual dataset utilities for cloud-native access to NASA Earthdata granules.

This subpackage provides tools for creating virtual xarray Datasets from
NASA Earthdata granules without downloading data, using VirtualiZarr parsers.

Public API
----------
- ``virtualize`` — create a virtual (or loaded) xarray Dataset from granules.
- ``SUPPORTED_PARSERS`` — frozenset of recognised parser name strings.
- ``get_granule_credentials_endpoint_and_region`` — resolve S3 credentials
  for a granule (useful for advanced direct-access workflows).

Requires the ``earthaccess[virtualizarr]`` optional extra.
"""

from __future__ import annotations

from earthaccess.virtual._credentials import (
    get_granule_credentials_endpoint_and_region,
)
from earthaccess.virtual._parser import SUPPORTED_PARSERS
from earthaccess.virtual.core import virtualize

__all__ = [
    "SUPPORTED_PARSERS",
    "get_granule_credentials_endpoint_and_region",
    "virtualize",
]
