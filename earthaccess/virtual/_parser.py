"""Parser resolution and URL generation for VirtualiZarr-backed virtual datasets.

This module is intentionally free of I/O side-effects.  It only resolves parser
names/instances and maps granule data links to the URLs the chosen parser needs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from earthaccess.virtual._types import AccessType, ParserType

if TYPE_CHECKING:
    import xarray as xr

    import earthaccess
    from earthaccess.virtual._types import AccessType, ParserType


logger = logging.getLogger(__name__)

# Canonical VirtualiZarr parser class names accepted by resolve_parser().
SUPPORTED_PARSERS: frozenset[str] = frozenset(
    {
        "DMRPPParser",
        "HDFParser",
        "NetCDF3Parser",
        "KerchunkJSONParser",
        "KerchunkParquetParser",
    },
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
        ``virtualizarr.open_virtual_mfdataset``.

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
            KerchunkJSONParser,
            KerchunkParquetParser,
            NetCDF3Parser,
        )
    except ImportError:
        msg = (
            "earthaccess.virtualize() requires `pip install earthaccess[virtualizarr]`"
        )
        raise ImportError(msg) from None

    # Normalise to canonical name (try aliases for lowercase input).
    canonical = _ALIASES.get(parser, parser)

    if canonical not in SUPPORTED_PARSERS:
        msg = (
            f"Unknown parser {parser!r}. "
            f"Supported parsers: {sorted(SUPPORTED_PARSERS)}. "
            "You can also pass a pre-built parser instance directly."
        )
        raise ValueError(msg)

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


def homogenize_dataset_codec_level(ds: xr.Dataset, target_level: int = 7) -> xr.Dataset:
    """Patch Zlib codec levels on all ManifestArrays in *ds* to *target_level*."""
    try:
        import xarray as xr
        from virtualizarr.manifests import ManifestArray
    except ImportError:
        raise ImportError(
            "earthaccess.virtualize() requires `pip install earthaccess[virtualizarr]`",
        ) from None

    def _patch_ma(ma: ManifestArray, level: int) -> ManifestArray:
        if not isinstance(ma, ManifestArray):
            return ma

        meta = ma.metadata
        codecs = list(meta.codecs)
        modified = False

        for i, codec in enumerate(codecs):
            if not hasattr(codec, "to_dict"):
                continue
            cd = codec.to_dict()
            if cd.get("name") != "numcodecs.zlib":
                continue
            cfg = cd.get("configuration", {})
            if cfg.get("level") == level:
                continue
            cd["configuration"] = {**cfg, "level": level}
            codecs[i] = type(codec).from_dict(cd)
            modified = True

        if not modified:
            return ma

        import zarr

        new_meta = zarr.core.metadata.v3.ArrayV3Metadata(
            shape=meta.shape,
            data_type=meta.data_type,
            chunk_grid=meta.chunk_grid,
            chunk_key_encoding=meta.chunk_key_encoding,
            fill_value=meta.fill_value,
            codecs=tuple(codecs),
            attributes=meta.attributes,
            dimension_names=meta.dimension_names,
            storage_transformers=meta.storage_transformers,
        )
        return ManifestArray(new_meta, ma.manifest)

    new_vars = {
        name: (
            xr.DataArray(
                _patch_ma(var.data, target_level),
                dims=var.dims,
                attrs=var.attrs,
                name=name,
            )
            if isinstance(var.data, ManifestArray)
            else var
        )
        for name, var in ds.data_vars.items()
    }

    return xr.Dataset(new_vars, coords=ds.coords, attrs=ds.attrs)
