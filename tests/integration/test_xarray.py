import fsspec
import h5netcdf
import xarray
from dask.distributed import Client
from earthaccess.store import EarthAccessFile


def test_open_dataset():
    fs = fsspec.filesystem("memory")
    values = list(range(32))
    fs_path = "foo"
    with fs.open(fs_path, mode="wb") as path:
        with h5netcdf.File(path, "w") as f:
            f.dimensions = {"x": len(values)}
            f.create_variable("data", ("x",), dtype="i4")
            f.variables["data"][:] = values
    f = fs.open(fs_path)
    earthaccess_file = EarthAccessFile(f, granule="foo")
    # confirm backend detection
    backends = xarray.backends.list_engines()
    assert backends["h5netcdf"].guess_can_open(earthaccess_file)
    # confirm opens
    ds = xarray.open_dataset(earthaccess_file)
    assert (ds["data"] == values).all()
    # confirm serializes
    client = Client()
    future = client.submit(xarray.open_dataset, earthaccess_file)
    ds = future.result()
    assert isinstance(ds, xarray.Dataset)
    # cleanup
    client.shutdown()
    fs.store.clear()
