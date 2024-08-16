from __future__ import annotations

from typing import TYPE_CHECKING

import earthaccess

if TYPE_CHECKING:
    import fsspec
    import xarray as xr


def _parse_dmr(
    fs: fsspec.AbstractFileSystem,
    data_path: str,
    dmrpp_path: str = None,
    group: str | None = None,
) -> xr.Dataset:
    """Parse a granule's DMR++ file and return a virtual xarray dataset.

    Parameters
    ----------
    fs : fsspec.AbstractFileSystem
        The file system to use to open the DMR++
    data_path : str
        The path to the data file
    dmrpp_path : str
        The path to the DMR++ file. If None, the DMR++ file is assumed to be at data_path + ".dmrpp"
    group : str
        The group to open in the DMR++.

    Returns:
    ----------
    xr.Dataset
        The virtual dataset (with virtualizarr ManifestArrays)

    Raises:
    ----------
    Exception if the DMR++ file is not found or if there is an error parsing the DMR++
    """
    from earthaccess.dmrpp import DMRParser

    dmrpp_path = data_path + ".dmrpp" if dmrpp_path is None else dmrpp_path
    with fs.open(dmrpp_path) as f:
        parser = DMRParser(f.read(), data_filepath=data_path)
    return parser.parse_dataset(group=group)


def open_virtual_mfdataset(
    granules: list[earthaccess.results.DataGranule],
    group: str | None = None,
    access: str = "indirect",
    load: bool = False,
    preprocess: callable | None = None,
    parallel: bool = True,
    **xr_combine_nested_kwargs,
) -> xr.Dataset:
    """Open multiple granules as a single virtual xarray Dataset.

    Parameters
    ----------
    granules : list[earthaccess.results.DataGranule]
        The granules to open
    group : str
        The group to open in the DMR++. If groups are present in the DMR++ files, this will open the specified group. If None, the first parsed group will be opened.
        If the DMR++ file does not have groups, this parameter is ignored.
    access : str
        The access method to use. One of "direct" or "indirect". Direct is for S3/cloud access, indirect is for HTTPS access.
    load: bool
        Create an xarray dataset with indexes and data available to load.

        When true, creates a lazy loaded, numpy/dask backed xarray dataset with indexes. Note that when load=True all the data is now available to access but not loaded into memory. When false a virtual xarray dataset is created with ManifestArrays. This virtual dataset is a view over the underlying metadata and chunks and allows creation and concatenation of zarr reference files. This virtual dataset cannot load data on it's own and see https://virtualizarr.readthedocs.io/en/latest/ for more information on virtual xarray datasets. Also note that load=True will only work in the cloud since ranged reads of chunks are supported by cloud storage but not by HTTPS
    preprocess : callable
        A function to apply to each virtual dataset before combining
    parallel : bool
        Whether to open the virtual datasets in parallel (using dask.delayed)
    xr_combine_nested_kwargs : dict
        Keyword arguments for xarray.combine_nested.
        See https://docs.xarray.dev/en/stable/generated/xarray.combine_nested.html

    Returns:
    ----------
    xr.Dataset

    Example:
    ----------
    >>> results = earthaccess.search_data(count=5, short_name="MUR-JPL-L4-GLOB-v4.1")
    >>> vds = open_virtual_mfdataset(results, access="indirect", load=False, concat_dim="time", coords='minimal', compat='override', combine_attrs="drop_conflicts")
    >>> vds
    <xarray.Dataset> Size: 19GB
    Dimensions:           (time: 5, lat: 17999, lon: 36000)
    Coordinates:
        time              (time) int32 20B ManifestArray<shape=(5,), dtype=int32,...
        lat               (lat) float32 72kB ManifestArray<shape=(17999,), dtype=...
        lon               (lon) float32 144kB ManifestArray<shape=(36000,), dtype...
    Data variables:
        mask              (time, lat, lon) int8 3GB ManifestArray<shape=(5, 17999...
        sea_ice_fraction  (time, lat, lon) int8 3GB ManifestArray<shape=(5, 17999...
        analysed_sst      (time, lat, lon) int16 6GB ManifestArray<shape=(5, 1799...
        analysis_error    (time, lat, lon) int16 6GB ManifestArray<shape=(5, 1799...
    Attributes: (12/41)
        Conventions:                CF-1.5
        title:                      Daily MUR SST, Final product
    """
    import xarray as xr

    if access == "indirect" and load:
        raise ValueError("load=True is not supported with access='indirect'")

    if access == "direct":
        fs = earthaccess.get_s3_filesystem(results=granules)
        fs.storage_options["anon"] = False
    else:
        fs = earthaccess.get_fsspec_https_session()
    if parallel:
        # wrap _open_virtual_dataset and preprocess with delayed
        import dask

        open_ = dask.delayed(_parse_dmr)
        if preprocess is not None:
            preprocess = dask.delayed(preprocess)
    else:
        open_ = _parse_dmr
    # data_paths: list[str] = []
    vdatasets = []
    for g in granules:
        # data_paths.append(g.data_links(access=access)[0])
        vdatasets.append(
            open_(fs=fs, group=group, data_path=g.data_links(access=access)[0])
        )
    # Rename paths to match granule s3/https paths
    # vdatasets = [
    # vds.virtualize.rename_paths(data_paths[i]) for i, vds in enumerate(vdatasets)
    # ]
    if preprocess is not None:
        vdatasets = [preprocess(ds) for ds in vdatasets]
    if parallel:
        vdatasets = dask.compute(vdatasets)[0]
    if len(vdatasets) == 1:
        vds = vdatasets[0]
    else:
        vds = xr.combine_nested(vdatasets, **xr_combine_nested_kwargs)
    if load:
        options = fs.storage_options.copy()
        refs = vds.virtualize.to_kerchunk(filepath=None, format="dict")
        options["fo"] = refs
        return xr.open_dataset(
            "reference://",
            engine="zarr",
            chunks={},
            backend_kwargs={"storage_options": options, "consolidated": False},
        )
    return vds


def open_virtual_dataset(
    granule: earthaccess.results.DataGranule,
    group: str | None = None,
    access: str = "indirect",
    load: bool = True,
) -> xr.Dataset:
    """Open a granule as a single virtual xarray Dataset.

    Parameters
    ----------
    granule : earthaccess.results.DataGranule
        The granule to open
    group : str
        The group to open in the DMR++. If groups are present in the DMR++ files, this will open the specified group. If None, the first parsed group will be opened.
        If the DMR++ file does not have groups, this parameter is ignored.
    access : str
        The access method to use. One of "direct" or "indirect". Direct is for S3/cloud access, indirect is for HTTPS access.
    load: bool
        When true, creates a numpy/dask backed xarray dataset. When false a virtual xarray dataset is created with ManifestArrays
        This virtual dataset cannot load data and is used to create zarr reference files. See https://virtualizarr.readthedocs.io/en/latest/
        for more information on virtual xarray datasets

    Returns:
    ----------
    xr.Dataset

    Example:
    ----------
    >>> results = earthaccess.search_data(count=2, temporal=("2023"), short_name="SWOT_L2_LR_SSH_Expert_2.0")
    >>> open_virtual_dataset(results[0], access="indirect", load=False)
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

    >>> results = earthaccess.search_data(count=2, short_name="ATL03")
    >>> open_virtual_dataset(results[0], group=""/gt1r/geolocation"" access="indirect", load=False)
    <xarray.Dataset> Size: 27MB
    Dimensions:                  (delta_time: 149696, ds_surf_type: 5, ds_xyz: 3)
    Coordinates:
        delta_time               (delta_time) float64 1MB ManifestArray<shape=(14...
        reference_photon_lon     (delta_time) float64 1MB ManifestArray<shape=(14...
        reference_photon_lat     (delta_time) float64 1MB ManifestArray<shape=(14...
    Dimensions without coordinates: ds_surf_type, ds_xyz
    Data variables: (12/34)
        surf_type                (delta_time, ds_surf_type) int8 748kB ManifestAr...
        podppd_flag              (delta_time) int8 150kB ManifestArray<shape=(149...
        segment_ph_cnt           (delta_time) int32 599kB ManifestArray<shape=(14...
    """
    return open_virtual_mfdataset(
        granules=[granule],
        group=group,
        access=access,
        load=load,
        parallel=False,
        preprocess=None,
    )
