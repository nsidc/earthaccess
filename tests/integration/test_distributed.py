import fsspec
from dask.distributed import Client
from earthaccess.store import EarthAccessFile


def test_serialization():
    fs = fsspec.filesystem("memory")
    foo = "foo"
    bar = b"bar"
    with fs.open(foo, mode="wb") as f:
        f.write(bar)
    f = fs.open(foo, mode="rb")
    earthaccess_file = EarthAccessFile(f, granule=foo)
    client = Client()
    future = client.submit(lambda f: f.read(), earthaccess_file)
    assert future.result() == bar
    # cleanup
    client.shutdown()
    fs.store.clear()
