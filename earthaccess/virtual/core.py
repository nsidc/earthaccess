"""Core implementation of ``earthaccess.virtualize()``.

This module contains the single public entry point for creating virtual
xarray Datasets from NASA Earthdata granules.
"""

from __future__ import annotations

import logging
import tempfile
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import earthaccess
from earthaccess.virtual._credentials import build_obstore_registry
from earthaccess.virtual._parser import get_urls_for_parser, resolve_parser

if TYPE_CHECKING:
    from collections.abc import Callable

    import xarray as xr

    from earthaccess.virtual._types import (
        AccessType,
        CombineAttrsType,
        CompatType,
        DataVarsType,
        ParallelType,
        ParserType,
        ReferenceFormatType,
    )


logger = logging.getLogger(__name__)


def virtualize(
    granules: list[earthaccess.DataGranule],
    *,
    access: AccessType = "direct",
    load: bool = False,
    group: str = "/",
    concat_dim: str | None = None,
    preprocess: Callable[[xr.Dataset], xr.Dataset] | None = None,
    data_vars: DataVarsType = "all",
    coords: str = "different",
    compat: CompatType = "no_conflicts",
    combine_attrs: CombineAttrsType = "drop_conflicts",
    parallel: ParallelType = "dask",
    parser: ParserType = "DMRPPParser",
    reference_dir: str | None = None,
    reference_format: ReferenceFormatType = "json",
    **xr_combine_kwargs: Any,
) -> xr.Dataset:
    """Create a virtual xarray Dataset from NASA Earthdata granules.

    Uses VirtualiZarr to open granules as virtual datasets backed by cloud
    object storage without downloading data.  By default returns a virtual
    dataset (``load=False``); set ``load=True`` to return a concrete
    lazily-loaded xarray Dataset via a kerchunk round-trip.

    The ``parser`` controls which VirtualiZarr backend reads the files.  The
    default ``"DMRPPParser"`` is the fastest option and uses NASA pre-computed
    DMR++ sidecar files.  When those sidecars are absent earthaccess
    automatically falls back to ``"HDFParser"`` and emits a ``UserWarning``.

    Parameters:
        granules: One or more ``DataGranule`` objects from
            ``earthaccess.search_data()``.
        access: Cloud access mode.  ``"direct"`` uses S3 (fastest inside AWS
            us-west-2); ``"indirect"`` uses HTTPS (works anywhere).
        load: When ``False`` (default) returns a virtual dataset with
            ``ManifestArray`` variables.  When ``True`` materialises the
            references via a kerchunk round-trip and returns a concrete,
            lazily-loaded ``xr.Dataset`` backed by dask arrays.
        group: HDF5/NetCDF4 group path to open.  Defaults to the root
            group ``"/"``.
        concat_dim: Dimension name used to concatenate granules.  Required
            when ``len(granules) > 1``.
        preprocess: Optional callable applied to each single-granule virtual
            dataset before combining.
        data_vars: Forwarded to ``xarray.combine_nested``.
        coords: Forwarded to ``xarray.combine_nested``.
        compat: Forwarded to ``xarray.combine_nested``.
        combine_attrs: Forwarded to ``xarray.combine_nested``.
        parallel: Parallelism backend.  ``"dask"`` (default) wraps opens in
            ``dask.delayed``; ``"lithops"`` uses Lithops; ``False`` disables
            parallelism.
        parser: VirtualiZarr parser to use.  One of ``"DMRPPParser"``
            (default), ``"HDFParser"``, ``"NetCDF3Parser"``, a lowercase alias
            (``"dmrpp"``, ``"hdf"``, ``"hdf5"``, ``"netcdf3"``), or a
            pre-instantiated parser object.
        reference_dir: Directory for kerchunk reference files when
            ``load=True``.  A temporary directory is used when ``None``.
        reference_format: Serialisation format when ``load=True``.
            ``"json"`` (default) or ``"parquet"``.
        **xr_combine_kwargs: Additional keyword arguments forwarded to
            ``xarray.combine_nested``.

    Returns:
        An ``xr.Dataset``.  With ``load=False`` the dataset contains
        ``ManifestArray`` variables; with ``load=True`` it contains dask
        arrays backed by the kerchunk reference store.

    Raises:
        ValueError: If ``granules`` is empty.
        ValueError: If ``len(granules) > 1`` and ``concat_dim`` is ``None``.
        ValueError: If ``parser`` is an unrecognised string.
        ImportError: If ``earthaccess[virtualizarr]`` is not installed.

    Examples:
        ```python
        import earthaccess

        granules = earthaccess.search_data(
            count=5,
            temporal=("2024-01-01", "2024-01-05"),
            short_name="MUR-JPL-L4-GLOB-v4.1",
        )

        # Virtual dataset (no data downloaded)
        vds = earthaccess.virtualize(granules, access="indirect", concat_dim="time")
        vds.virtualize.to_kerchunk("mur_combined.json", format="json")

        # Loaded dataset (kerchunk round-trip, lazy dask arrays)
        ds = earthaccess.virtualize(granules, access="direct", load=True, concat_dim="time")
        ```
    """
    if len(granules) == 0:
        raise ValueError("No granules provided. At least one granule is required.")
    if len(granules) > 1 and concat_dim is None:
        raise ValueError(
            "concat_dim is required when virtualizing more than one granule. "
            "Pass concat_dim='<dimension_name>' to specify how to concatenate.",
        )

    # Validate / resolve parser early so callers get a clear error before any
    # network activity.
    resolved_parser = resolve_parser(parser, group=group if group != "/" else None)

    registry = build_obstore_registry(granules, access=access)

    # Attempt to open with the requested parser; fall back to HDFParser if
    # DMR++ sidecars are not present.
    try:
        vds = _open_virtual_mfdataset(
            granules=granules,
            parser=resolved_parser,
            registry=registry,
            access=access,
            concat_dim=concat_dim,
            preprocess=preprocess,
            parallel=parallel,
            data_vars=data_vars,
            coords=coords,
            compat=compat,
            combine_attrs=combine_attrs,
            **xr_combine_kwargs,
        )
    except FileNotFoundError:
        if type(resolved_parser).__name__ != "DMRPPParser":
            raise
        warnings.warn(
            "DMR++ sidecar files were not found for one or more granules. "
            "Falling back to HDFParser. "
            "Set parser='HDFParser' to silence this warning.",
            UserWarning,
            stacklevel=2,
        )
        resolved_parser = resolve_parser(
            "HDFParser",
            group=group if group != "/" else None,
        )
        registry = build_obstore_registry(granules, access=access)
        vds = _open_virtual_mfdataset(
            granules=granules,
            parser=resolved_parser,
            registry=registry,
            access=access,
            concat_dim=concat_dim,
            preprocess=preprocess,
            parallel=parallel,
            data_vars=data_vars,
            coords=coords,
            compat=compat,
            combine_attrs=combine_attrs,
            **xr_combine_kwargs,
        )

    if not load:
        return vds

    return _load_via_kerchunk(
        vds=vds,
        granules=granules,
        group=group,
        access=access,
        reference_dir=reference_dir,
        reference_format=reference_format,
    )


# ---------------------------------------------------------------------------
# Internal helpers — separated to make mocking clean in tests
# ---------------------------------------------------------------------------


def _open_virtual_mfdataset(
    granules: list[earthaccess.DataGranule],
    parser: Any,
    registry: Any,
    access: AccessType,
    concat_dim: str | None,
    preprocess: Callable | None,
    parallel: ParallelType,
    data_vars: DataVarsType,
    coords: str,
    compat: CompatType,
    combine_attrs: CombineAttrsType,
    **xr_combine_kwargs: Any,
) -> xr.Dataset:
    """Thin wrapper around ``vz.open_virtual_mfdataset`` for testability."""
    try:
        import virtualizarr as vz
    except ImportError as exc:
        raise ImportError(
            "earthaccess.virtualize() requires `pip install earthaccess[virtualizarr]`",
        ) from exc

    urls = get_urls_for_parser(granules, parser, access=access)

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Numcodecs codecs*",
            category=UserWarning,
        )
        return vz.open_virtual_mfdataset(
            urls=urls,
            registry=registry,
            parser=parser,
            preprocess=preprocess,
            parallel=parallel,
            combine="nested",
            concat_dim=concat_dim,
            data_vars=data_vars,
            coords=coords,
            compat=compat,
            combine_attrs=combine_attrs,
            **xr_combine_kwargs,
        )


def _load_via_kerchunk(
    vds: xr.Dataset,
    granules: list[earthaccess.DataGranule],
    group: str,
    access: AccessType,
    reference_dir: str | None,
    reference_format: ReferenceFormatType,
) -> xr.Dataset:
    """Materialise a virtual dataset coordinates for "fancy" slicing via a kerchunk round-trip.

    Needed until https://github.com/zarr-developers/VirtualiZarr/issues/360
    is resolved. TODO: make sure this holds, I think this may have been resolved already.
    """
    import xarray as xr

    fs = earthaccess.get_fsspec_https_session()

    if reference_dir is None:
        ref_dir = Path(tempfile.gettempdir())
    else:
        ref_dir = Path(reference_dir)
        ref_dir.mkdir(exist_ok=True, parents=True)

    collection_id = granules[0]["meta"]["collection-concept-id"]

    if group in (None, "/"):
        group_name = "root"
    else:
        group_name = group.replace("/", "_").replace(" ", "_").lstrip("_")

    ref_path = ref_dir / f"{collection_id}-{group_name}.{reference_format}"

    # Round-trip: write kerchunk reference, then reopen with xarray.
    vds.virtualize.to_kerchunk(str(ref_path), format=reference_format)

    storage_options = {
        "remote_protocol": "s3" if access == "direct" else "https",
        "remote_options": fs.storage_options,
    }
    return xr.open_dataset(
        str(ref_path),
        engine="kerchunk",
        storage_options=storage_options,
    )
