from __future__ import annotations

import tempfile
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlparse

import earthaccess

if TYPE_CHECKING:
    import xarray as xr


def open_virtual_mfdataset(
    granules: list[earthaccess.DataGranule],
    group: str | None = None,
    access: str = "indirect",
    preprocess: callable | None = None,  # type: ignore
    parallel: Literal["dask", "lithops", False] = "dask",
    load: bool = True,
    reference_dir: str | None = None,
    reference_format: Literal["json", "parquet"] = "json",
    **xr_combine_nested_kwargs: Any,
) -> xr.Dataset:
    """Open multiple granules as a single virtual xarray Dataset.

    Uses NASA DMR++ metadata files to create a virtual xarray dataset with ManifestArrays. This virtual dataset can be used to create zarr reference files. See [https://virtualizarr.readthedocs.io](https://virtualizarr.readthedocs.io) for more information on virtual xarray datasets.

    > WARNING: This feature is current experimental and may change in the future. This feature relies on DMR++ metadata files which may not always be present for your dataset and you may get a `FileNotFoundError`.

    Parameters:
        granules:
            The granules to open
        group:
            Path to the netCDF4 group in the given file to open. If None, the root group will be opened. If the DMR++ file does not have groups, this parameter is ignored.
        access:
            The access method to use. One of "direct" or "indirect". Use direct when running on AWS, use indirect when running on a local machine.
        preprocess:
            A function to apply to each virtual dataset before combining
        parallel:
            Open the virtual datasets in parallel (using dask.delayed or lithops)
        load:
            If load is True, earthaccess will serialize the virtual references in order to use lazy indexing on the resulting xarray virtual ds.
        reference_dir:
            Directory to store kerchunk references. If None, a temporary directory will be created and deleted after use.
        reference_format:
            When load is True, earthaccess will serialize the references using this format, json (default) or parquet.
        xr_combine_nested_kwargs:
            Xarray arguments describing how to concatenate the datasets. Keyword arguments for xarray.combine_nested.
            See [https://docs.xarray.dev/en/stable/generated/xarray.combine_nested.html](https://docs.xarray.dev/en/stable/generated/xarray.combine_nested.html)

    Returns:
        Concatenated xarray.Dataset

    Examples:
        ```python
        >>> results = earthaccess.search_data(count=5, temporal=("2024"), short_name="MUR-JPL-L4-GLOB-v4.1")
        >>> vds = earthaccess.open_virtual_mfdataset(results, access="indirect", load=False, concat_dim="time", coords="minimal", compat="override", combine_attrs="drop_conflicts")
        >>> vds
        <xarray.Dataset> Size: 29GB
        Dimensions:           (time: 5, lat: 17999, lon: 36000)
        Coordinates:
            time              (time) int32 20B ManifestArray<shape=(5,), dtype=int32,...
            lat               (lat) float32 72kB ManifestArray<shape=(17999,), dtype=...
            lon               (lon) float32 144kB ManifestArray<shape=(36000,), dtype...
        Data variables:
            mask              (time, lat, lon) int8 3GB ManifestArray<shape=(5, 17999...
            sea_ice_fraction  (time, lat, lon) int8 3GB ManifestArray<shape=(5, 17999...
            dt_1km_data       (time, lat, lon) int8 3GB ManifestArray<shape=(5, 17999...
            analysed_sst      (time, lat, lon) int16 6GB ManifestArray<shape=(5, 1799...
            analysis_error    (time, lat, lon) int16 6GB ManifestArray<shape=(5, 1799...
            sst_anomaly       (time, lat, lon) int16 6GB ManifestArray<shape=(5, 1799...
        Attributes: (12/42)
            Conventions:                CF-1.7
            title:                      Daily MUR SST, Final product

        >>> vds.virtualize.to_kerchunk("mur_combined.json", format="json")
        >>> vds = open_virtual_mfdataset(results, access="indirect", concat_dim="time", coords='minimal', compat='override', combine_attrs="drop_conflicts")
        >>> vds
        <xarray.Dataset> Size: 143GB
        Dimensions:           (time: 5, lat: 17999, lon: 36000)
        Coordinates:
        * lat               (lat) float32 72kB -89.99 -89.98 -89.97 ... 89.98 89.99
        * lon               (lon) float32 144kB -180.0 -180.0 -180.0 ... 180.0 180.0
        * time              (time) datetime64[ns] 40B 2024-01-01T09:00:00 ... 2024-...
        Data variables:
            analysed_sst      (time, lat, lon) float64 26GB dask.array<chunksize=(1, 3600, 7200), meta=np.ndarray>
            analysis_error    (time, lat, lon) float64 26GB dask.array<chunksize=(1, 3600, 7200), meta=np.ndarray>
            dt_1km_data       (time, lat, lon) timedelta64[ns] 26GB dask.array<chunksize=(1, 4500, 9000), meta=np.ndarray>
            mask              (time, lat, lon) float32 13GB dask.array<chunksize=(1, 4500, 9000), meta=np.ndarray>
            sea_ice_fraction  (time, lat, lon) float64 26GB dask.array<chunksize=(1, 4500, 9000), meta=np.ndarray>
            sst_anomaly       (time, lat, lon) float64 26GB dask.array<chunksize=(1, 3600, 7200), meta=np.ndarray>
        Attributes: (12/42)
            Conventions:                CF-1.7
            title:                      Daily MUR SST, Final product
        ```
    """
    try:
        import virtualizarr as vz
        import xarray as xr
        from obstore.auth.earthdata import NasaEarthdataCredentialProvider
        from obstore.store import HTTPStore, S3Store
        from virtualizarr.parsers import DMRPPParser
        from virtualizarr.registry import ObjectStoreRegistry
    except ImportError as e:
        raise ImportError(
            "`earthaccess.open_virtual_dataset` requires `pip install earthaccess[virtualizarr]`"
        ) from e

    if len(granules) == 0:
        raise ValueError("No granules provided. At least one granule is required.")

    parsed_url = urlparse(granules[0].data_links(access=access)[0])
    fs = earthaccess.get_fsspec_https_session()
    if len(granules):
        collection_id = granules[0]["meta"]["collection-concept-id"]

    if access == "direct":
        credentials_endpoint, region = get_granule_credentials_endpoint_and_region(
            granules[0]
        )
        bucket = parsed_url.netloc

        if load:
            fs = earthaccess.get_s3_filesystem(endpoint=credentials_endpoint)

        s3_store = S3Store(
            bucket=bucket,
            region=region,
            credential_provider=NasaEarthdataCredentialProvider(credentials_endpoint),
            virtual_hosted_style_request=False,
            client_options={"allow_http": True},
        )
        obstore_registry = ObjectStoreRegistry({f"s3://{bucket}": s3_store})
    else:
        domain = parsed_url.netloc
        http_store = HTTPStore.from_url(
            f"https://{domain}",
            client_options={
                "default_headers": {
                    "Authorization": f"Bearer {earthaccess.__auth__.token['access_token']}",
                },
            },
        )
        obstore_registry = ObjectStoreRegistry({f"https://{domain}": http_store})

    granule_dmrpp_urls = [
        granule.data_links(access=access)[0] + ".dmrpp" for granule in granules
    ]

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Numcodecs codecs*",
            category=UserWarning,
        )
        vmfdataset = vz.open_virtual_mfdataset(
            urls=granule_dmrpp_urls,
            registry=obstore_registry,
            parser=DMRPPParser(group=group),
            preprocess=preprocess,
            parallel=parallel,
            combine="nested",
            **xr_combine_nested_kwargs,
        )

    if load:
        if reference_dir is None:
            ref_dir = Path(tempfile.gettempdir())
        else:
            ref_dir = Path(reference_dir)
            ref_dir.mkdir(exist_ok=True, parents=True)  # type: ignore

        if group is None or group == "/":
            group_name = "root"
        else:
            group_name = group.replace("/", "_").replace(" ", "_").lstrip("_")

        ref_ = ref_dir / Path(f"{collection_id}-{group_name}.{reference_format}")
        # We still need the round trip because: https://github.com/zarr-developers/VirtualiZarr/issues/360
        vmfdataset.virtualize.to_kerchunk(str(ref_), format=reference_format)

        storage_options = {
            "remote_protocol": "s3" if access == "direct" else "https",
            "remote_options": fs.storage_options,
        }
        vds = xr.open_dataset(
            str(ref_),
            engine="kerchunk",
            storage_options=storage_options,
        )
        return vds

    return vmfdataset


def open_virtual_dataset(
    granule: earthaccess.DataGranule,
    load: bool = True,
    group: str | None = None,
    access: str = "indirect",
) -> xr.Dataset:
    """Open a granule as a single virtual xarray Dataset.

    Uses NASA DMR++ metadata files to create a virtual xarray dataset with ManifestArrays. This virtual dataset can be used to create zarr reference files. See [https://virtualizarr.readthedocs.io](https://virtualizarr.readthedocs.io) for more information on virtual xarray datasets.

    > WARNING: This feature is current experimental and may change in the future. This feature relies on DMR++ metadata files which may not always be present for your dataset and you may get a `FileNotFoundError`.

    Parameters:
        granule:
            The granule to open
        group:
            Path to the netCDF4 group in the given file to open. If None, the root group will be opened. If the DMR++ file does not have groups, this parameter is ignored.
        access:
            The access method to use. One of "direct" or "indirect". Use direct when running on AWS, use indirect when running on a local machine.

    Returns:
        xarray.Dataset

    Examples:
        ```python
        >>> results = earthaccess.search_data(count=2, temporal=("2023"), short_name="SWOT_L2_LR_SSH_Expert_2.0")
        >>> vds =  earthaccess.open_virtual_dataset(results[0], access="indirect")
        >>> vds
        <xarray.Dataset> Size: 149MB
        Dimensions:                                (num_lines: 9866, num_pixels: 69,
                                                    num_sides: 2)
        Coordinates:
            longitude                              (num_lines, num_pixels) int32 3MB ...
            latitude                               (num_lines, num_pixels) int32 3MB ...
            latitude_nadir                         (num_lines) int32 39kB ManifestArr...
            longitude_nadir                        (num_lines) int32 39kB ManifestArr...
        Dimensions without coordinates: num_lines, num_pixels, num_sides
        Data variables: (12/98)
            height_cor_xover_qual                  (num_lines, num_pixels) uint8 681kB ManifestArray<shape=(9866, 69), dtype=uint8, chunks=(9866, 69...
        >>> vds.virtualize.to_kerchunk("swot_2023_ref.json", format="json")
        ```
    """
    return open_virtual_mfdataset(
        granules=[granule],
        load=load,
        group=group,
        access=access,
        parallel=False,
        preprocess=None,
    )


def get_granule_credentials_endpoint_and_region(
    granule: earthaccess.DataGranule,
) -> tuple[str, str]:
    """Retrieve credentials endpoint for direct access granule link.

    Parameters:
        granule:
            The first granule being included in the virtual dataset.

    Returns:
        credentials_endpoint:
            The S3 credentials endpoint. If this information is in the UMM-G record, then it is used from there. If not, a query for the collection is performed and the information is taken from the UMM-C record.
        region:
            Region for the data. Defaults to us-west-2. If the credentials endpoint is retrieved from the UMM-C record for the collection, the Region information is also used from UMM-C.

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
        raise ValueError("The collection did not provide an S3CredentialsAPIEndpoint")

    return credentials_endpoint, region
