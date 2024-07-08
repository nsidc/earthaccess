from pathlib import Path

import earthaccess
import pytest
from fsspec.core import strip_protocol

kerchunk = pytest.importorskip("kerchunk")
pytest.importorskip("dask")


@pytest.mark.parametrize("protocol", ["", "file://"])
def test_consolidate_metadata_outfile(tmp_path, granules, protocol):
    outfile = f"{protocol}{tmp_path / 'metadata.json'}"
    assert not Path(outfile).exists()
    result = earthaccess.consolidate_metadata(
        granules,
        outfile=outfile,
        access="indirect",
        kerchunk_options={"concat_dims": "Time"},
    )
    assert Path(strip_protocol(outfile)).exists()
    assert result == outfile


def test_consolidate_metadata_memory(tmp_path, granules):
    result = earthaccess.consolidate_metadata(
        granules,
        access="indirect",
        kerchunk_options={"concat_dims": "Time"},
    )
    assert isinstance(result, dict)
    assert "refs" in result


@pytest.mark.parametrize("output", ["file", "memory"])
def test_consolidate_metadata(tmp_path, granules, output):
    xr = pytest.importorskip("xarray")
    # Open directly with `earthaccess.open`
    expected = xr.open_mfdataset(earthaccess.open(granules))

    # Open with kerchunk consolidated metadata file
    if output == "file":
        kwargs = {"outfile": tmp_path / "metadata.json"}
    else:
        kwargs = {}
    metadata = earthaccess.consolidate_metadata(
        granules, access="indirect", kerchunk_options={"concat_dims": "Time"}, **kwargs
    )

    fs = earthaccess.get_fsspec_https_session()
    result = xr.open_dataset(
        "reference://",
        engine="zarr",
        chunks={},
        backend_kwargs={
            "consolidated": False,
            "storage_options": {
                "fo": metadata,
                "remote_protocol": "https",
                "remote_options": fs.storage_options,
            },
        },
    )

    xr.testing.assert_equal(result, expected)
