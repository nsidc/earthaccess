from __future__ import annotations

from typing import Optional, Union

import fsspec
import fsspec.utils
import s3fs

# import ipdb
import earthaccess


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
