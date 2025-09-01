from __future__ import annotations

from typing import TYPE_CHECKING, Any

import earthaccess

if TYPE_CHECKING:
    import xarray as xr


def open_virtual_mfdataset(
    granules: list[earthaccess.DataGranule],
    group: str | None = None,
    access: str = "indirect",
    load: bool = False,
    preprocess: callable | None = None,  # type: ignore
    parallel: bool = True,
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
        load:
            Create an xarray dataset with indexes and lazy loaded data.

            When true, creates a lazy loaded, numpy/dask backed xarray dataset with indexes. Note that when `load=True` all the data is now available to access but not loaded into memory. When `load=False` a virtual xarray dataset is created with ManifestArrays. This virtual dataset is a view over the underlying metadata and chunks and allows creation and concatenation of zarr reference files. This virtual dataset cannot load data on it's own and see https://virtualizarr.readthedocs.io/en/latest/ for more information on virtual xarray datasets.
        preprocess:
            A function to apply to each virtual dataset before combining
        parallel:
            Open the virtual datasets in parallel (using dask.delayed)
        xr_combine_nested_kwargs:
            Xarray arguments describing how to concatenate the datasets. Keyword arguments for xarray.combine_nested.
            See [https://docs.xarray.dev/en/stable/generated/xarray.combine_nested.html](https://docs.xarray.dev/en/stable/generated/xarray.combine_nested.html)

    Returns:
        Concatenated xarray.Dataset

    Examples:
        ```python
        >>> results = earthaccess.search_data(count=5, temporal=("2024"), short_name="MUR-JPL-L4-GLOB-v4.1")
        >>> vds = earthaccess.open_virtual_mfdataset(results, access="indirect", load=False, concat_dim="time", coords='minimal', compat='override', combine_attrs="drop_conflicts")
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
        >>> vds = open_virtual_mfdataset(results, access="indirect", load=True, concat_dim="time", coords='minimal', compat='override', combine_attrs="drop_conflicts")
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
    import virtualizarr as vz
    import xarray as xr

    if access == "direct":
        fs = earthaccess.get_s3_filesystem(results=granules)  # type: ignore
        fs.storage_options["anon"] = False
    else:
        fs = earthaccess.get_fsspec_https_session()
    if parallel:
        import dask

        # wrap _open_virtual_dataset and preprocess with delayed
        open_ = dask.delayed(vz.open_virtual_dataset)  # type: ignore
        if preprocess is not None:
            preprocess = dask.delayed(preprocess)  # type: ignore
    else:
        open_ = vz.open_virtual_dataset  # type: ignore
    vdatasets = []
    # Get list of virtual datasets (or dask delayed objects)
    for g in granules:
        vdatasets.append(
            open_(
                filepath=g.data_links(access=access)[0] + ".dmrpp",
                filetype="dmrpp",  # type: ignore
                group=group,
                indexes={},
                reader_options={"storage_options": fs.storage_options},
            )
        )
    if preprocess is not None:
        vdatasets = [preprocess(ds) for ds in vdatasets]
    if parallel:
        vdatasets = dask.compute(vdatasets)[0]  # type: ignore
    if len(vdatasets) == 1:
        vds = vdatasets[0]
    else:
        vds = xr.combine_nested(vdatasets, **xr_combine_nested_kwargs)
    if load:
        refs = vds.virtualize.to_kerchunk(filepath=None, format="dict")
        protocol = "s3" if "s3" in fs.protocol else fs.protocol
        return xr.open_dataset(
            "reference://",
            engine="zarr",
            chunks={},
            backend_kwargs={
                "consolidated": False,
                "storage_options": {
                    "fo": refs,  # codespell:ignore
                    "remote_protocol": protocol,
                    "remote_options": fs.storage_options,
                },
            },
        )
    return vds


def open_virtual_dataset(
    granule: earthaccess.DataGranule,
    group: str | None = None,
    access: str = "indirect",
    load: bool = False,
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
        load:
            Create an xarray dataset with indexes and lazy loaded data.

            When true, creates a lazy loaded, numpy/dask backed xarray dataset with indexes. Note that when `load=True` all the data is now available to access but not loaded into memory. When `load=False` a virtual xarray dataset is created with ManifestArrays. This virtual dataset is a view over the underlying metadata and chunks and allows creation and concatenation of zarr reference files. This virtual dataset cannot load data on it's own and see https://virtualizarr.readthedocs.io/en/latest/ for more information on virtual xarray datasets.

    Returns:
        xarray.Dataset

    Examples:
        ```python
        >>> results = earthaccess.search_data(count=2, temporal=("2023"), short_name="SWOT_L2_LR_SSH_Expert_2.0")
        >>> vds =  earthaccess.open_virtual_dataset(results[0], access="indirect", load=False)
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
        group=group,
        access=access,
        load=load,
        parallel=False,
        preprocess=None,
    )
