from __future__ import annotations

from typing import Any

import earthaccess
import fsspec
import s3fs

try:
    from kerchunk.combine import MultiZarrToZarr
    from kerchunk.hdf import SingleHdf5ToZarr
except ImportError as e:
    raise ImportError(
        "`earthaccess.consolidate_metadata` requires `kerchunk` to be be installed"
    ) from e


try:
    from dask import compute, delayed
except ImportError:
    # Dask isn't installed, so let's just define a couple of
    # small API-compatible noops

    def delayed(func: Any) -> Any:
        return func

    def compute(*args: Any, **kwargs: Any) -> Any:
        return args


@delayed
def get_chunk_metadata(
    granuale: earthaccess.results.DataGranule,
    fs: fsspec.AbstractFileSystem | s3fs.S3FileSystem,
) -> list[dict]:
    metadata = []
    access = "direct" if isinstance(fs, s3fs.S3FileSystem) else "indirect"
    for url in granuale.data_links(access=access):
        print(f"{url = }")
        with fs.open(url) as inf:
            h5chunks = SingleHdf5ToZarr(inf, url)
            m = h5chunks.translate()
            metadata.append(m)
    return metadata


def consolidate_metadata(
    granuales: list[earthaccess.results.DataGranule],
    outfile: str,
    storage_options: dict | None = None,
    kerchunk_options: dict | None = None,
    access: str = "direct",
) -> str:
    if access == "direct":
        fs = earthaccess.get_s3fs_session(provider=granuales[0]["meta"]["provider-id"])
    else:
        fs = earthaccess.get_fsspec_https_session()

    # Write out metadata file for each granuale
    chunks = compute(*[get_chunk_metadata(g, fs) for g in granuales])
    chunks = sum(chunks, start=[])

    # Write combined metadata file
    mzz = MultiZarrToZarr(chunks, **kerchunk_options)
    mzz.translate(outfile, storage_options=storage_options or {})

    return outfile
