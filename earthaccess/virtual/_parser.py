"""Parser resolution and URL generation for VirtualiZarr-backed virtual datasets.

This module is intentionally free of I/O side-effects.  It only resolves parser
names/instances and maps granule data links to the URLs the chosen parser needs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from earthaccess.virtual._types import AccessType, ParserType

if TYPE_CHECKING:
    import earthaccess

logger = logging.getLogger(__name__)

# Canonical VirtualiZarr parser class names accepted by resolve_parser().
SUPPORTED_PARSERS: frozenset[str] = frozenset(
    {
        "DMRPPParser",
        "HDFParser",
        "NetCDF3Parser",
        "KerchunkJSONParser",
        "KerchunkParquetParser",
    }
)

# Maps user-facing lowercase aliases → canonical class name.
_ALIASES: dict[str, str] = {
    "dmrpp": "DMRPPParser",
    "hdf": "HDFParser",
    "hdf5": "HDFParser",
    "netcdf3": "NetCDF3Parser",
    "kerchunk": "KerchunkJSONParser",
    "kerchunk-parquet": "KerchunkParquetParser",
}


def resolve_parser(
    parser: ParserType,
    group: str | None = None,
) -> Any:
    """Resolve a parser name or instance to a VirtualiZarr parser object.

    If ``parser`` is already an instance (i.e. not a ``str``) it is returned
    unchanged.  String values are matched case-sensitively against
    ``SUPPORTED_PARSERS`` first, then against the lowercase aliases table.

    Parameters:
        parser: A canonical parser name, a lowercase alias, or a pre-built
            parser instance.
        group: HDF5/NetCDF4 group path forwarded to the parser constructor.
            Ignored when ``parser`` is a pre-built instance.

    Returns:
        An instantiated VirtualiZarr parser ready to be passed to
        ``vz.open_virtual_mfdataset``.

    Raises:
        ValueError: If ``parser`` is a string not in ``SUPPORTED_PARSERS`` and
            not a recognised alias.
        ImportError: If ``earthaccess[virtualizarr]`` is not installed.
    """
    if not isinstance(parser, str):
        # Pre-built instance — return unchanged (duck-typed, no validation).
        return parser

    try:
        from virtualizarr.parsers import (
            DMRPPParser,
            HDFParser,
            NetCDF3Parser,
            KerchunkJSONParser,
            KerchunkParquetParser,
        )
    except ImportError as exc:
        raise ImportError(
            "earthaccess.virtualize() requires `pip install earthaccess[virtualizarr]`"
        ) from exc

    # Normalise to canonical name (try aliases for lowercase input).
    canonical = _ALIASES.get(parser, parser)

    if canonical not in SUPPORTED_PARSERS:
        raise ValueError(
            f"Unknown parser {parser!r}. "
            f"Supported parsers: {sorted(SUPPORTED_PARSERS)}. "
            "You can also pass a pre-built parser instance directly."
        )

    _parser_map = {
        "DMRPPParser": lambda: DMRPPParser(group=group),
        "HDFParser": lambda: HDFParser(group=group),
        "NetCDF3Parser": lambda: NetCDF3Parser(group=group),
        "KerchunkJSONParser": lambda: KerchunkJSONParser(group=group),
        "KerchunkParquetParser": lambda: KerchunkParquetParser(group=group),
    }
    return _parser_map[canonical]()


def get_urls_for_parser(
    granules: list[earthaccess.DataGranule],
    parser: Any,
    access: AccessType,
) -> list[str]:
    """Return one data URL per granule, formatted for the given parser.

    ``DMRPPParser`` expects the NASA DMR++ sidecar files, which live at the
    data URL with a ``.dmrpp`` suffix appended.  All other parsers receive the
    raw data URLs as-is.

    Parameters:
        granules: The granules to generate URLs for.
        parser: A resolved (instantiated) parser object.
        access: ``"direct"`` (S3) or ``"indirect"`` (HTTPS).  Forwarded to
            ``DataGranule.data_links()``.

    Returns:
        A list of URL strings, one per granule.
    """
    is_dmrpp = type(parser).__name__ == "DMRPPParser"

    urls: list[str] = []
    for granule in granules:
        url = granule.data_links(access=access)[0]
        if is_dmrpp:
            url = url + ".dmrpp"
        urls.append(url)
    return urls
