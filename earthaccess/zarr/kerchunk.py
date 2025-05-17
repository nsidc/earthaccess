from __future__ import annotations

from typing import Optional, Union

import logging

import fsspec
import fsspec.utils
import s3fs

# import ipdb
import earthaccess
from uuid import uuid4
import zipfile
from pathlib import Path
import json

logger = logging.getLogger(__name__)


def _get_chunk_metadata(
    granule: earthaccess.DataGranule,
    fs: fsspec.AbstractFileSystem,
) -> list[dict]:
    from kerchunk.hdf import SingleHdf5ToZarr

    if not isinstance(granule, earthaccess.DataGranule) and isinstance(granule, dict):
        # WHY: dask serialization is doing something weird, it serializes the granule as a simple dict
        # we need to add cast it back to a datagranule to get the nice methods for parsing the data links
        # TODO: ask James what is going on
        granule = earthaccess.DataGranule(granule)

    metadata = []
    access = "direct" if isinstance(fs, s3fs.S3FileSystem) else "indirect"
    # ipdb.set_trace()

    for url in granule.data_links(access=access):
        with fs.open(url) as inf:
            h5chunks = SingleHdf5ToZarr(inf, url)  # type: ignore
            m = h5chunks.translate()
            metadata.append(m)

    return metadata


def consolidate_metadata(
    granules: list[earthaccess.DataGranule],
    kerchunk_options: Optional[dict] = None,
    access: str = "direct",
    outfile: Optional[str] = None,
    storage_options: Optional[dict] = None,
) -> Union[str, dict]:
    try:
        import dask

        from kerchunk.combine import MultiZarrToZarr
    except ImportError as e:
        raise ImportError(
            "`earthaccess.consolidate_metadata` requires `dask` and `kerchunk` to be be installed"
        ) from e

    if access == "direct":
        fs = earthaccess.get_s3_filesystem(provider=granules[0]["meta"]["provider-id"])
    else:
        fs = earthaccess.get_fsspec_https_session()

    # Get metadata for each granule
    get_chunk_metadata = dask.delayed(_get_chunk_metadata)  # type: ignore

    # ipdb.set_trace()
    chunks = dask.compute(*[get_chunk_metadata(g, fs) for g in granules])  # type: ignore
    chunks = sum(chunks, start=[])

    # Get combined metadata object
    mzz = MultiZarrToZarr(chunks, **(kerchunk_options or {}))

    if outfile is None:
        return mzz.translate()

    output = fsspec.utils.stringify_path(outfile)
    mzz.translate(outfile, storage_options=storage_options or {})
    return output

def get_virtual_reference(short_name: str = "",
                          cloud_hosted: bool=True,
                          format: str ="parquet") -> Union[fsspec.FSMap, None]:
    """
    Returns a virtual reference file for a given collection, this reference has to be created by the DAAC
    distributing the data. The reference mapper can be used directly in xarray as a Zarr store.
    """

    file_types = {
        "parquet": "parq.zip",
        "json": "json",
    }

    
    # Find collection-level metadata (UMM-C) on CMR:
    collections = earthaccess.search_datasets(short_name=short_name, cloud_hosted=cloud_hosted)

    links = collections[0]["umm"].get("RelatedUrls", [])

    # Look within UMM-C for links to virtual data set reference files:
    # I think both json or parquet should be under VIRTUAL COLLECTION
    refs = [e["URL"] for e in links if "Subtype" in e and (("VIRTUAL COLLECTION" in e["Subtype"]) or ("DATA RECIPE" in e["Subtype"]))]
    

    # Currently it is assumed that link descriptions have the following format:
    if refs:
        logger.info("Virtual data set reference file exists for this collection")
        link = [link for link in refs if link.endswith(file_types[format])][0]
    else:
        logger.info(
            "Virtual data set reference file does not exists in",
            "There may be a reference file in a different format, or else you will have to",
            "open this data set using traditional netCDF/HDF methods."
            )
        return None

    # this assumes the ref point to s3 links, we'll have to refactor later
    http_fs = earthaccess.get_fsspec_https_session()
    fs = earthaccess.get_s3_filesystem(provider=collections[0]["meta"]["provider-id"])
    if link.endswith(".json"):
        with http_fs.open(link) as f:
            ref_loc = json.load(f)
    else:
        with http_fs.open(link, 'rb') as remote_zip:
            # Unzip the contents into the temporary directory
            with zipfile.ZipFile(remote_zip, 'r') as zip_ref:
                id = uuid4()
                local_path = Path(f".references/{id}")
                zip_ref.extractall(local_path)
                ref_loc = str([d for d in local_path.iterdir() if d.is_dir()][0])

    storage_opts = {"fo": ref_loc, 
                    "remote_protocol": "s3", 
                    "remote_options": fs.storage_options}
    file_ref = fsspec.filesystem('reference', **storage_opts)
    return file_ref.get_mapper('')
