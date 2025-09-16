import fsspec
import xarray as xr
from earthaccess.store import EarthAccessFile


def test_open_dataset():
    ds = xr.Dataset({"y": ("x", list(range(8)))})
    fs = fsspec.filesystem("memory")
    path = "foo"
    with fs.open(path, mode="wb") as f:
        ds.to_netcdf(f, engine="h5netcdf")
    f = fs.open(path)
    earthaccess_file = EarthAccessFile(f, granule="foo")
    # confirm backend detection
    backends = xr.backends.list_engines()
    assert backends["h5netcdf"].guess_can_open(earthaccess_file)
    # confirm opens correctly
    assert (xr.open_dataset(earthaccess_file) == ds).all()
    # cleanup
    fs.store.clear()
