"""Unit tests for earthaccess.virtual._parser.

Written TDD-first: these tests are written against the public contract of
``_parser.py`` before the implementation exists.  Run them with::

    pytest tests/unit/test_virtual_parser.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_granule(url: str) -> MagicMock:
    g = MagicMock()
    g.data_links.return_value = [url]
    return g


# ---------------------------------------------------------------------------
# SUPPORTED_PARSERS
# ---------------------------------------------------------------------------


def test_supported_parsers_is_frozenset() -> None:
    from earthaccess.virtual._parser import SUPPORTED_PARSERS

    assert isinstance(SUPPORTED_PARSERS, frozenset)


def test_supported_parsers_contains_canonical_names() -> None:
    from earthaccess.virtual._parser import SUPPORTED_PARSERS

    assert "DMRPPParser" in SUPPORTED_PARSERS
    assert "HDFParser" in SUPPORTED_PARSERS
    assert "NetCDF3Parser" in SUPPORTED_PARSERS


# ---------------------------------------------------------------------------
# resolve_parser – canonical string names
# ---------------------------------------------------------------------------


def test_resolve_parser_dmrpp_returns_instance() -> None:
    from earthaccess.virtual._parser import resolve_parser

    parser = resolve_parser("DMRPPParser")
    assert type(parser).__name__ == "DMRPPParser"


def test_resolve_parser_hdfparser_returns_instance() -> None:
    from earthaccess.virtual._parser import resolve_parser

    parser = resolve_parser("HDFParser")
    assert type(parser).__name__ == "HDFParser"


def test_resolve_parser_netcdf3_returns_instance() -> None:
    from earthaccess.virtual._parser import resolve_parser

    parser = resolve_parser("NetCDF3Parser")
    assert type(parser).__name__ == "NetCDF3Parser"


# ---------------------------------------------------------------------------
# resolve_parser – group forwarding
# ---------------------------------------------------------------------------


def test_resolve_parser_group_forwarded_to_dmrpp() -> None:
    from earthaccess.virtual._parser import resolve_parser

    parser = resolve_parser("DMRPPParser", group="/science")
    assert parser.group == "/science"


def test_resolve_parser_group_forwarded_to_hdf() -> None:
    from earthaccess.virtual._parser import resolve_parser

    parser = resolve_parser("HDFParser", group="/data")
    assert parser.group == "/data"


def test_resolve_parser_group_forwarded_to_netcdf3() -> None:
    from earthaccess.virtual._parser import resolve_parser

    parser = resolve_parser("NetCDF3Parser", group="/g")
    assert parser.group == "/g"


# ---------------------------------------------------------------------------
# resolve_parser – lowercase aliases
# ---------------------------------------------------------------------------


def test_resolve_parser_lowercase_alias_dmrpp() -> None:
    from earthaccess.virtual._parser import resolve_parser

    assert type(resolve_parser("dmrpp")).__name__ == "DMRPPParser"


def test_resolve_parser_lowercase_alias_hdf5() -> None:
    from earthaccess.virtual._parser import resolve_parser

    assert type(resolve_parser("hdf5")).__name__ == "HDFParser"


def test_resolve_parser_lowercase_alias_hdf() -> None:
    from earthaccess.virtual._parser import resolve_parser

    assert type(resolve_parser("hdf")).__name__ == "HDFParser"


def test_resolve_parser_lowercase_alias_netcdf3() -> None:
    from earthaccess.virtual._parser import resolve_parser

    assert type(resolve_parser("netcdf3")).__name__ == "NetCDF3Parser"


# ---------------------------------------------------------------------------
# resolve_parser – pass-through instance
# ---------------------------------------------------------------------------


def test_resolve_parser_accepts_instance_passthrough() -> None:
    from earthaccess.virtual._parser import resolve_parser

    mock_parser = MagicMock()
    result = resolve_parser(mock_parser)
    assert result is mock_parser


# ---------------------------------------------------------------------------
# resolve_parser – error cases
# ---------------------------------------------------------------------------


def test_resolve_parser_invalid_string_raises() -> None:
    from earthaccess.virtual._parser import resolve_parser

    with pytest.raises(ValueError, match="UnknownParser"):
        resolve_parser("UnknownParser")


def test_resolve_parser_error_message_lists_valid_parsers() -> None:
    from earthaccess.virtual._parser import resolve_parser

    with pytest.raises(ValueError, match="DMRPPParser"):
        resolve_parser("bad")


# ---------------------------------------------------------------------------
# get_urls_for_parser
# ---------------------------------------------------------------------------


def test_get_urls_dmrpp_appends_dmrpp_suffix() -> None:
    from earthaccess.virtual._parser import get_urls_for_parser, resolve_parser

    granules = [_make_mock_granule("s3://bucket/file.nc")]
    parser = resolve_parser("DMRPPParser")
    urls = get_urls_for_parser(granules, parser, access="direct")
    assert urls == ["s3://bucket/file.nc.dmrpp"]


def test_get_urls_hdf_returns_raw_url() -> None:
    from earthaccess.virtual._parser import get_urls_for_parser, resolve_parser

    granules = [_make_mock_granule("https://data.nasa.gov/file.h5")]
    parser = resolve_parser("HDFParser")
    urls = get_urls_for_parser(granules, parser, access="indirect")
    assert urls == ["https://data.nasa.gov/file.h5"]


def test_get_urls_netcdf3_returns_raw_url() -> None:
    from earthaccess.virtual._parser import get_urls_for_parser, resolve_parser

    granules = [_make_mock_granule("https://data.nasa.gov/file.nc")]
    parser = resolve_parser("NetCDF3Parser")
    urls = get_urls_for_parser(granules, parser, access="indirect")
    assert urls == ["https://data.nasa.gov/file.nc"]


def test_get_urls_multiple_granules_returns_one_per_granule() -> None:
    from earthaccess.virtual._parser import get_urls_for_parser, resolve_parser

    granules = [
        _make_mock_granule("s3://bucket/a.nc"),
        _make_mock_granule("s3://bucket/b.nc"),
    ]
    parser = resolve_parser("HDFParser")
    urls = get_urls_for_parser(granules, parser, access="direct")
    assert len(urls) == 2
    assert urls[0] == "s3://bucket/a.nc"
    assert urls[1] == "s3://bucket/b.nc"


def test_get_urls_dmrpp_multiple_granules() -> None:
    from earthaccess.virtual._parser import get_urls_for_parser, resolve_parser

    granules = [
        _make_mock_granule("s3://bucket/a.nc"),
        _make_mock_granule("s3://bucket/b.nc"),
    ]
    parser = resolve_parser("DMRPPParser")
    urls = get_urls_for_parser(granules, parser, access="direct")
    assert urls == ["s3://bucket/a.nc.dmrpp", "s3://bucket/b.nc.dmrpp"]


def test_get_urls_passes_access_to_data_links() -> None:
    from earthaccess.virtual._parser import get_urls_for_parser, resolve_parser

    granule = _make_mock_granule("https://example.com/file.h5")
    parser = resolve_parser("HDFParser")
    get_urls_for_parser([granule], parser, access="indirect")
    granule.data_links.assert_called_once_with(access="indirect")
