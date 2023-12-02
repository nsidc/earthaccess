from __future__ import annotations

import fsspec
import s3fs

import earthaccess


def _get_chunk_metadata(
    granuale: earthaccess.results.DataGranule,
    fs: fsspec.AbstractFileSystem | s3fs.S3FileSystem,
) -> list[dict]:
    from kerchunk.hdf import SingleHdf5ToZarr

    metadata = []
    access = "direct" if isinstance(fs, s3fs.S3FileSystem) else "indirect"
    for url in granuale.data_links(access=access):
        with fs.open(url) as inf:
            h5chunks = SingleHdf5ToZarr(inf, url)
            m = h5chunks.translate()
            metadata.append(m)
    return metadata


def consolidate_metadata(
    granuales: list[earthaccess.results.DataGranule],
    kerchunk_options: dict | None = None,
    access: str = "direct",
    outfile: str | None = None,
    storage_options: dict | None = None,
) -> str | dict:
    try:
        import dask

        from kerchunk.combine import MultiZarrToZarr
    except ImportError as e:
        raise ImportError(
            "`earthaccess.consolidate_metadata` requires `dask` and `kerchunk` to be be installed"
        ) from e

    if access == "direct":
        fs = earthaccess.get_s3fs_session(provider=granuales[0]["meta"]["provider-id"])
    else:
        fs = earthaccess.get_fsspec_https_session()

    # Get metadata for each granuale
    get_chunk_metadata = dask.delayed(_get_chunk_metadata)
    chunks = dask.compute(*[get_chunk_metadata(g, fs) for g in granuales])
    chunks = sum(chunks, start=[])

    # Get combined metadata object
    mzz = MultiZarrToZarr(chunks, **(kerchunk_options or {}))
    if outfile is not None:
        output = fsspec.utils.stringify_path(outfile)
        mzz.translate(outfile, storage_options=storage_options or {})
        return output
    else:
        return mzz.translate()
