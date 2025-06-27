import h5netcdf
import io
import xarray
from earthaccess.store import EarthAccessFile
import fsspec
def test_open_dataset():
    buffer = io.BytesIO()
    with h5netcdf.File(buffer, 'w') as f:
        f.dimensions = {'x': 3}
        f.create_variable('data', ('x',), dtype='i4')
        f.variables['data'][:] = xarray.DataArray([1, 2, 3])
    fs = fsspec.filesystem("memory")
    fs_path = "mydir/myfile.h5"
    fs.pipe(fs_path, buffer.getvalue())
    with fs.open(fs_path, mode="rb") as f:
        earthaccess_file = EarthAccessFile(f, granule="foo")
        assert xarray.backends.list_engines()["h5netcdf"].guess_can_open(earthaccess_file)
        file = xarray.open_dataset(earthaccess_file, engine="h5netcdf")
        assert  xarray.DataArray.all(file["data"].values == xarray.DataArray([1, 2, 3]))
    fs.store.clear()