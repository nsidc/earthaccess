from __future__ import annotations

from typing import TYPE_CHECKING

import earthaccess

if TYPE_CHECKING:
    import xarray as xr


def open_virtual_mfdataset(
    granules: list[earthaccess.results.DataGranule],
    access: str = "indirect",
    load: bool = True,
    preprocess: callable | None = None,
    parallel: bool = True,
    **xr_combine_nested_kwargs,
) -> xr.Dataset:
    """
    Open multiple granules as a single virtual xarray Dataset

    Parameters
    ----------
    granules : list[earthaccess.results.DataGranule]
        The granules to open
    access : str
        The access method to use. One of "direct" or "indirect". Direct is for S3/cloud access, indirect is for HTTPS access.
    load: bool
        When true, creates a lazy loaded, numpy/dask backed xarray dataset with indexes. When false a virtual xarray dataset is created with ManifestArrays. This virtual dataset cannot load data and is used to create zarr reference files. See https://virtualizarr.readthedocs.io/en/latest/ for more information on virtual xarray datasets
    preprocess : callable
        A function to apply to each virtual dataset before combining
    parallel : bool
        Whether to open the virtual datasets in parallel (using dask.delayed)
    xr_combine_nested_kwargs : dict
        Keyword arguments for xarray.combine_nested.
        See https://docs.xarray.dev/en/stable/generated/xarray.combine_nested.html

    Returns
    ----------
    xr.Dataset
        The virtual dataset
    """
    import xarray as xr

    import virtualizarr as vz

    if access == "direct":
        fs = earthaccess.get_s3fs_session(results=granules)
        fs.storage_options["anon"] = False
    else:
        fs = earthaccess.get_fsspec_https_session()
    if parallel:
        # wrap _open_virtual_dataset and preprocess with delayed
        import dask

        open_ = dask.delayed(vz.open_virtual_dataset)
        if preprocess is not None:
            preprocess = dask.delayed(preprocess)
    else:
        open_ = vz.open_virtual_dataset
    data_paths: list[str] = []
    vdatasets = []
    for g in granules:
        data_paths.append(g.data_links(access=access)[0])
        vdatasets.append(
            open_(
                filepath=g.data_links(access=access)[0] + ".dmrpp",
                filetype="dmrpp",
                reader_options={"storage_options": fs.storage_options},
            )
        )
    # Rename paths to match granule s3/https paths
    vdatasets = [
        vds.virtualize.rename_paths(data_paths[i]) for i, vds in enumerate(vdatasets)
    ]
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
    access: str = "indirect",
    load: bool = True,
) -> xr.Dataset:
    """
    Open a granule as a single virtual xarray Dataset

    Parameters
    ----------
    granule : earthaccess.results.DataGranule
        The granule to open
    access : str
        The access method to use. One of "direct" or "indirect". Direct is for S3/cloud access, indirect is for HTTPS access.
    load: bool
        When true, creates a numpy/dask backed xarray dataset. When false a virtual xarray dataset is created with ManifestArrays
        This virtual dataset cannot load data and is used to create zarr reference files. See https://virtualizarr.readthedocs.io/en/latest/
        for more information on virtual xarray datasets

    Returns
    ----------
    xr.Dataset
        The virtual dataset
    """
    return open_virtual_mfdataset(
        granules=[granule], access=access, load=load, parallel=False, preprocess=None
    )
