from __future__ import annotations

import fsspec
import xarray as xr

import earthaccess


def _parse_dmr(
    fs: fsspec.AbstractFileSystem,
    data_path: str,
    dmr_path: str = None
) -> xr.Dataset:
    """
    Parse a granule's DMR++ file and return a virtual xarray dataset

    Parameters
    ----------
    granule : earthaccess.results.DataGranule
        The granule to parse
        fs : fsspec.AbstractFileSystem
        The file system to use to open the DMR++

    Returns
    ----------
    xr.Dataset
    The virtual dataset (with virtualizarr ManifestArrays)

    Raises
    ----------
    Exception
    If the DMR++ file is not found or if there is an error parsing the DMR++
    """
    from virtualizarr.readers.dmrpp import DMRParser

    dmr_path = data_path + ".dmrpp" if dmr_path is None else dmr_path
    with fs.open(dmr_path) as f:
        parser = DMRParser(f.read(), data_filepath=data_path)
    return parser.parse()


def open_virtual_mfdataset(
    granules: list[earthaccess.results.DataGranule],
    access: str = "indirect",
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
    xr_combine_nested_kwargs : dict
        Keyword arguments for xarray.combine_nested.
        See https://docs.xarray.dev/en/stable/generated/xarray.combine_nested.html

    Returns
    ----------
    xr.Dataset
        The virtual dataset
    """
    if access == "direct":
        fs = earthaccess.get_s3fs_session(results=granules)
    else:
        fs = earthaccess.get_fsspec_https_session()
    if parallel:
        # wrap _parse_dmr and preprocess with delayed
        import dask
        open_ = dask.delayed(_parse_dmr)
        if preprocess is not None:
            preprocess = dask.delayed(preprocess)
    else:
        open_ = _parse_dmr
    vdatasets = [open_(fs=fs, data_path=g.data_links(access=access)[0]) for g in granules]
    if preprocess is not None:
        vdatasets = [preprocess(ds) for ds in vdatasets]
    if parallel:
        vdatasets = dask.compute(vdatasets)[0]
    if len(vdatasets) == 1:
        vds = vdatasets[0]
    else:
        vds = xr.combine_nested(vdatasets, **xr_combine_nested_kwargs)
    return vds


def open_virtual_dataset(
    granule: earthaccess.results.DataGranule, access: str = "indirect"
) -> xr.Dataset:
    """
    Open a granule as a single virtual xarray Dataset

    Parameters
    ----------
    granule : earthaccess.results.DataGranule
        The granule to open
    access : str
        The access method to use. One of "direct" or "indirect". Direct is for S3/cloud access, indirect is for HTTPS access.

    Returns
    ----------
    xr.Dataset
        The virtual dataset
    """
    return open_virtual_mfdataset(
        granules=[granule], access=access, parallel=False, preprocess=None
    )

