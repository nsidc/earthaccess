"""Core implementation of ``earthaccess.virtualize()`` and ``earthaccess.open_virtual()``.

This module contains public entry points for creating virtual xarray
Datasets from NASA Earthdata granules and opening existing virtual stores.
"""

from __future__ import annotations

import json
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


def virtualize(  # noqa: PLR0913
    granules: list[earthaccess.DataGranule],
    *,
    access: AccessType = "indirect",
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
        access: Cloud access mode.  ``"indirect"`` (default) uses HTTPS
            (works anywhere); ``"direct"`` uses S3 (fastest inside AWS
            us-west-2 but requires S3 credentials).
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
        msg = "No granules provided. At least one granule is required."
        raise ValueError(msg)
    if len(granules) > 1 and concat_dim is None:
        msg = (
            "concat_dim is required when virtualizing more than one granule. "
            "Pass concat_dim='<dimension_name>' to specify how to concatenate."
        )
        raise ValueError(msg)

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


def _open_virtual_mfdataset(  # noqa: PLR0913
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
        msg = (
            "earthaccess.virtualize() requires `pip install earthaccess[virtualizarr]`"
        )
        raise ImportError(msg) from exc

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


def _load_via_kerchunk(  # noqa: PLR0913
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


# ---------------------------------------------------------------------------
# open_virtual — open existing virtual stores (Icechunk / VirtualiZarr)
# ---------------------------------------------------------------------------


def _is_icechunk_uri(uri: str) -> bool:
    return uri.startswith("icechunk://") or uri.endswith(".icechunk")


def _is_kerchunk_uri(uri: str) -> bool:
    return uri.endswith((".parquet", ".json"))


def _open_icechunk(
    uri: str,
    storage_options: dict[str, Any] | None = None,
    **kwargs: Any,
) -> xr.Dataset:
    try:
        import icechunk
        import xarray as xr
    except ImportError as exc:
        msg = (
            "earthaccess.open_virtual() with an Icechunk store requires "
            "`pip install earthaccess[virtualizarr]`"
        )
        raise ImportError(
            msg,
        ) from exc

    if storage_options:
        storage = icechunk.http_storage(uri, storage_options)
    else:
        storage = icechunk.local_filesystem_storage(uri)

    repo = icechunk.Repository.open(storage=storage)
    session = repo.readonly_session("main")
    store = session.store
    return xr.open_zarr(store, **kwargs)


def _open_kerchunk(
    uri: str,
    storage_options: dict[str, Any] | None = None,
    **kwargs: Any,
) -> xr.Dataset:
    try:
        import xarray as xr
    except ImportError as exc:
        msg = "earthaccess.open_virtual() requires `pip install earthaccess[virtualizarr]`"
        raise ImportError(
            msg,
        ) from exc

    store_opts = storage_options or {}
    return xr.open_dataset(uri, engine="kerchunk", storage_options=store_opts, **kwargs)


# ---------------------------------------------------------------------------
# force_external — download kerchunk refs and rewrite s3:// URLs to https://
# ---------------------------------------------------------------------------


def _transform_refs(obj: Any, https_base: str) -> None:
    """Recursively walk a kerchunk refs dict/list and rewrite s3:// URLs in-place."""
    prefix = "s3://"
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith(prefix):
                obj[k] = https_base + v[len(prefix) :]
            elif isinstance(v, (dict, list)):
                _transform_refs(v, https_base)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and v.startswith(prefix):
                obj[i] = https_base + v[len(prefix) :]
            elif isinstance(v, (dict, list)):
                _transform_refs(v, https_base)


def _sanitize_references_for_external(url: str) -> str:
    """Download a kerchunk reference file, rewrite ``s3://`` URLs to ``https://``.

    The HTTPS base is inferred from the reference file URL's host, which works
    for all NASA Earthdata Cloud DAACs (PODAAC, NSIDC, GES DISC, LP DAAC, …).

    Returns the local path to the sanitized file.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if not parsed.scheme:
        return url

    local = Path(tempfile.gettempdir()) / f"external_{Path(url).name}"

    if local.exists():
        return str(local)

    host = parsed.netloc
    https_base = f"https://{host}/"
    fs = earthaccess.get_fsspec_https_session()

    if url.endswith(".json"):
        with fs.open(url, cache="first") as f:
            refs: dict[str, Any] = json.load(f)
        _transform_refs(refs, https_base)
        local.write_text(json.dumps(refs))

    elif url.endswith(".parquet"):
        import pandas as pd

        with fs.open(url, cache="first") as f:
            refs_df = pd.read_parquet(f)
        if "path" in refs_df.columns:
            mask = refs_df["path"].str.startswith("s3://", na=False)
            refs_df.loc[mask, "path"] = (
                https_base + refs_df.loc[mask, "path"].str[len("s3://") :]
            )
        refs_df.to_parquet(local)

    return str(local)


def _open_kerchunk_from_collection(
    collection: earthaccess.DataCollection,
    url: str,
    access: str = "indirect",
    **kwargs: Any,
) -> xr.Dataset:
    try:
        import fsspec
        import xarray as xr
        import zarr
    except ImportError as exc:
        msg = "earthaccess.open_virtual() requires `pip install earthaccess[virtualizarr]`"
        raise ImportError(
            msg,
        ) from exc

    if access == "direct":
        daac_fs = collection.get_s3_filesystem()
        remote_protocol = "s3"
    else:
        daac_fs = earthaccess.get_fsspec_https_session()
        remote_protocol = "https"

    remote_options = {"asynchronous": True, **daac_fs.storage_options}
    fs = fsspec.filesystem(
        "reference",
        fo=url,
        remote_protocol=remote_protocol,
        asynchronous=True,
        remote_options=remote_options,
    )
    store = zarr.storage.FsspecStore(fs, read_only=True)
    return xr.open_zarr(store, consolidated=False, **kwargs)


def _open_icechunk_from_collection(
    collection: earthaccess.DataCollection,
    url: str,
    access: str = "indirect",
    **kwargs: Any,
) -> xr.Dataset:
    try:
        from datetime import UTC, datetime, timedelta

        import icechunk
        import xarray as xr
    except ImportError as exc:
        msg = (
            "earthaccess.open_virtual() with an Icechunk store requires "
            "`pip install earthaccess[virtualizarr]`"
        )
        raise ImportError(
            msg,
        ) from exc

    if access == "direct":
        from urllib.parse import urlparse

        creds = collection.get_s3_credentials()
        ice_creds = icechunk.S3StaticCredentials(
            access_key_id=creds["accessKeyId"],
            secret_access_key=creds["secretAccessKey"],
            session_token=creds["sessionToken"],
            expires_after=datetime.now(UTC) + timedelta(hours=1),
        )
        parsed = urlparse(url)
        storage = icechunk.s3_storage(
            bucket=parsed.netloc,
            prefix=parsed.path.lstrip("/"),
            get_credentials=lambda: ice_creds,
        )
    else:
        storage = icechunk.redirect_storage(url)

    repo = icechunk.Repository.open(storage=storage)
    session = repo.readonly_session("main")
    store = session.store
    return xr.open_zarr(store, **kwargs)


# ---------------------------------------------------------------------------
# open_virtual via VirtualiZarr (load=False)
# ---------------------------------------------------------------------------


def _is_nasa_url(url: str) -> bool:
    """Return ``True`` if the URL belongs to a NASA Earthdata host."""
    return "nasa.gov" in url.lower()


def _build_registry_for_url(url: str) -> Any:
    """Build an ``ObjectStoreRegistry`` for the given reference file *url*.

    A ``LocalStore`` for ``file://`` is always registered so that local
    reference files can be read.  For remote URLs an authenticated
    ``HTTPStore`` is also registered so that referenced data files can
    be resolved with the user's EDL credentials.
    """
    from urllib.parse import urlparse

    try:
        from obspec_utils.registry import ObjectStoreRegistry
        from obstore.store import HTTPStore, LocalStore
    except ImportError:
        try:
            from virtualizarr.registry import (
                ObjectStoreRegistry,  # type: ignore[no-redef]
            )
        except ImportError:
            msg = (
                "earthaccess.open_virtual(load=False) requires "
                "`pip install earthaccess[virtualizarr]`"
            )
            raise ImportError(
                msg,
            ) from None

    stores: dict[str, Any] = {"file://": LocalStore.from_url("file:///")}

    parsed = urlparse(url)
    if parsed.scheme == "https":
        try:
            token = earthaccess.__auth__.token["access_token"]
        except (AttributeError, TypeError, KeyError):
            pass
        else:
            http_store = HTTPStore.from_url(
                f"https://{parsed.netloc}",
                client_options={
                    "default_headers": {"Authorization": f"Bearer {token}"},
                },
            )
            stores[f"https://{parsed.netloc}"] = http_store

    if not parsed.scheme or parsed.scheme == "file":
        path = Path(parsed.path).resolve()
        parent = path.parent if path.suffix else path
        file_prefix = parent.as_uri()
        stores[file_prefix] = LocalStore.from_url(file_prefix)

    return ObjectStoreRegistry(stores)


def _download_reference_file(url: str) -> str:
    """Download a remote reference file to a local cache (``/tmp/cached_*``).

    Returns the local path.  Already-local files are returned as-is.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if not parsed.scheme:
        return url

    local = Path(tempfile.gettempdir()) / f"cached_{Path(url).name}"
    if local.exists():
        return str(local)

    if _is_nasa_url(url):
        fs = earthaccess.get_fsspec_https_session()
    else:
        import fsspec

        fs = fsspec.filesystem("https")

    with fs.open(url) as src:
        local.write_bytes(src.read())
    return str(local)


def _open_virtual_via_virtualizarr(
    url: str,
    *,
    registry_url: str | None = None,
    **kwargs: Any,
) -> xr.Dataset:
    """Open a kerchunk reference file using VirtualiZarr (``load=False``).

    First the reference file is opened via an fsspec reference filesystem
    to load inline coordinate values, then VirtualiZarr virtualises the
    remaining data variables and the two results are merged.

    An ``ObjectStoreRegistry`` is automatically configured from
    *registry_url* (defaults to *url*) so that referenced data files can
    be resolved with the user's EDL credentials.

    For JSON files the reference file is first downloaded to a local cache;
    parquet files are read directly from their URL.
    """
    try:
        import fsspec
        import virtualizarr as vz
        import xarray as xr
        import zarr
        from virtualizarr.parsers import KerchunkJSONParser, KerchunkParquetParser
    except ImportError as exc:
        msg = (
            "earthaccess.open_virtual(load=False) requires "
            "`pip install earthaccess[virtualizarr]`"
        )
        raise ImportError(
            msg,
        ) from exc

    auth_url = registry_url or url
    registry = _build_registry_for_url(auth_url)

    ref_path = _download_reference_file(url) if url.endswith(".json") else url

    daac_fs = (
        earthaccess.get_fsspec_https_session()
        if _is_nasa_url(auth_url)
        else fsspec.filesystem("https")
    )
    remote_options = {"asynchronous": True, **daac_fs.storage_options}
    fs = fsspec.filesystem(
        "reference",
        fo=ref_path,
        remote_protocol="https",
        asynchronous=True,
        remote_options=remote_options,
    )
    store = zarr.storage.FsspecStore(fs, read_only=True)
    kds = xr.open_zarr(store, consolidated=False)

    parser: KerchunkJSONParser | KerchunkParquetParser
    if url.endswith(".json"):
        parser = KerchunkJSONParser(skip_variables=list(kds.coords))
    elif url.endswith(".parquet"):
        parser = KerchunkParquetParser(skip_variables=list(kds.coords))
    else:
        msg = (
            f"Unsupported virtual store format: {url}. "
            "Expected a .json or .parquet file."
        )
        raise ValueError(
            msg,
        )

    vds = vz.open_virtual_dataset(ref_path, parser=parser, registry=registry, **kwargs)

    for k in kds.coords:
        vds.coords[k] = kds[k]
    return vds


def open_virtual(  # noqa: PLR0911
    uri: str | Path | earthaccess.DataCollection,
    *,
    access: str = "indirect",
    storage_options: dict[str, Any] | None = None,
    force_external: bool = False,
    load: bool = True,
    **kwargs: Any,
) -> xr.Dataset:
    """Open a URI or collection as a virtual xarray Dataset.

    Supports two kinds of virtual stores:

    - **Icechunk** — a versioned Zarr store (``.icechunk`` file/URI).
    - **VirtualiZarr / kerchunk** — reference-file-backed datasets
      (``.parquet`` or ``.json`` files).

    When given a ``DataCollection``, the virtual store URL is extracted from
    its metadata (``GET DATA`` + ``VIRTUAL COLLECTION`` subtype).

    Parameters:
        uri: A ``DataCollection``, or a path/URI to the virtual store
            (``.icechunk``, ``.parquet``, or ``.json``).
        access: ``"indirect"`` (HTTPS, default) or ``"direct"`` (S3).
        storage_options: Additional options forwarded to the storage backend.
            Ignored when ``uri`` is a ``DataCollection``.
        force_external: When ``True``, download kerchunk reference files and
            rewrite ``s3://`` URLs to ``https://``, so the dataset can be
            opened without direct S3 access.  Only applies to ``.json`` and
            ``.parquet`` reference files.  Requires authentication.
        load: When ``True`` (default), returns a concrete lazily-loaded dataset
            via the kerchunk engine.  When ``False``, returns a virtual dataset
            backed by ``ManifestArray`` objects via VirtualiZarr's
            ``open_virtual_dataset``.
        **kwargs: Additional keyword arguments forwarded to the opener.

    Returns:
        An ``xr.Dataset`` backed by the virtual store.

    Raises:
        ValueError: If the URI is not recognised, or the collection has no
            virtual collection URL.
        ImportError: If the required optional dependency is not installed.
        AttributeError: If the user is not authenticated.

    Examples:
        >>> import earthaccess
        >>> ds = earthaccess.open_virtual("s3://bucket/refs.parquet")
        >>> ds = earthaccess.open_virtual("/local/store.icechunk")
        >>> ds = earthaccess.open_virtual(collection)
        >>> ds = earthaccess.open_virtual(collection, force_external=True)
    """
    if isinstance(uri, earthaccess.DataCollection):
        url = uri.virtual_collection_url()
        if url is None:
            msg = (
                f"Collection {uri.get('meta', {}).get('concept-id', '')} "
                "does not have a virtual store (no VIRTUAL COLLECTION "
                "URL found in its RelatedUrls)."
            )
            raise ValueError(
                msg,
            )
        if not _is_icechunk_uri(url) and not _is_kerchunk_uri(url):
            msg = (
                f"Unrecognised virtual store URL in collection: {url}. "
                "Expected a .icechunk, .parquet, or .json file."
            )
            raise ValueError(
                msg,
            )
    else:
        url = str(uri)

    if not _is_icechunk_uri(url) and not _is_kerchunk_uri(url):
        msg = (
            f"Unrecognised virtual store URI: {uri}. "
            "Expected a .icechunk, .parquet, or .json file/URI."
        )
        raise ValueError(
            msg,
        )

    if _is_icechunk_uri(url):
        if isinstance(uri, earthaccess.DataCollection):
            return _open_icechunk_from_collection(uri, url, access=access, **kwargs)
        return _open_icechunk(url, storage_options=storage_options, **kwargs)

    if not load:
        if force_external:
            sanitized = _sanitize_references_for_external(url)
            return _open_virtual_via_virtualizarr(sanitized, registry_url=url, **kwargs)
        return _open_virtual_via_virtualizarr(url, **kwargs)

    if force_external:
        sanitized = _sanitize_references_for_external(url)
        sopts = {
            "remote_protocol": "https",
            "remote_options": earthaccess.get_fsspec_https_session().storage_options,
        }
        return _open_kerchunk(sanitized, storage_options=sopts, **kwargs)

    if isinstance(uri, earthaccess.DataCollection):
        return _open_kerchunk_from_collection(uri, url, access=access, **kwargs)
    return _open_kerchunk(url, storage_options=storage_options, **kwargs)
