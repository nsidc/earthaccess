from __future__ import annotations

from dask.base import flatten
from dask.distributed import default_client, progress, Client, Worker, WorkerPlugin
from kerchunk.combine import MultiZarrToZarr
from kerchunk.hdf import SingleHdf5ToZarr

import earthaccess
from .auth import Auth


def get_chunk_metadata(
    granuale: earthaccess.results.DataGranule, access: str
) -> list[dict]:
    if access == "direct":
        fs_data = earthaccess.get_s3fs_session(provider=granuale["meta"]["provider-id"])
    else:
        fs_data = earthaccess.get_fsspec_https_session()

    metadata = []
    for url in granuale.data_links(access=access):
        with fs_data.open(url) as inf:
            h5chunks = SingleHdf5ToZarr(inf, url)
            m = h5chunks.translate()
            metadata.append(m)
    return metadata


class EarthAccessAuth(WorkerPlugin):
    name = "earthaccess-auth"

    def __init__(self, auth: Auth):
        self.auth = auth

    def setup(self, worker: Worker) -> None:
        if not earthaccess.__auth__.authenticated:
            earthaccess.__auth__ = self.auth
            earthaccess.login()


def consolidate_metadata(
    granuales: list[earthaccess.results.DataGranule],
    outfile: str,
    storage_options: dict | None = None,
    kerchunk_options: dict | None = None,
    access: str = "direct",
    client: Client | None = None,
) -> str:
    if client is None:
        client = default_client()

    # Make sure cluster is authenticated
    client.register_worker_plugin(EarthAccessAuth(earthaccess.__auth__))

    # Write out metadata file for each granuale
    futures = client.map(get_chunk_metadata, granuales, access=access)
    progress(futures)
    chunks = client.gather(futures)
    chunks = list(flatten(chunks))

    # Write combined metadata file
    mzz = MultiZarrToZarr(chunks, **kerchunk_options)
    mzz.translate(outfile, storage_options=storage_options or {})

    return outfile
