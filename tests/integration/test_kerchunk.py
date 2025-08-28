import logging
from pathlib import Path

import earthaccess
import pytest
from fsspec.core import strip_protocol

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def granules():
    return earthaccess.search_data(
        count=2,
        short_name="SEA_SURFACE_HEIGHT_ALT_GRIDS_L4_2SATS_5DAY_6THDEG_V_JPL2205",
        cloud_hosted=True,
    )


@pytest.mark.parametrize("protocol", ["", "file://"])
def test_consolidate_metadata_outfile(tmp_path, granules, protocol):
    outfile = f"{protocol}{tmp_path / 'metadata.json'}"
    result = earthaccess.consolidate_metadata(
        granules,
        outfile=outfile,
        access="indirect",
        kerchunk_options={"concat_dims": "Time"},
    )
    assert Path(strip_protocol(outfile)).exists()
    assert result == outfile


def test_consolidate_metadata_memory(granules):
    result = earthaccess.consolidate_metadata(
        granules,
        access="indirect",
        kerchunk_options={"concat_dims": "Time"},
    )
    assert isinstance(result, dict)
    assert "refs" in result


@pytest.mark.parametrize("output", ["file", "memory"])
def test_consolidate_metadata(tmp_path, granules, output):
    # We import here because xarray is installed only when the kerchunk extra is
    # installed, and when type checking is run, kerchunk (and thus xarray) is
    # not installed, so mypy barfs when this is a top-level import.  Further,
    # mypy complains even when imported here, but here we can mark it to ignore.
    import xarray as xr  # type: ignore

    # Open directly with `earthaccess.open`
    expected = xr.open_mfdataset(earthaccess.open(granules), engine="h5netcdf")

    # Open with kerchunk consolidated metadata file
    kwargs = {"outfile": tmp_path / "metadata.json"} if output == "file" else {}
    earthaccess.consolidate_metadata(
        granules, access="indirect", kerchunk_options={"concat_dims": "Time"}, **kwargs
    )

    fs = earthaccess.get_fsspec_https_session()
    # This test should be eventually refactored to use virtualizarr
    if output == "file":
        result = xr.open_dataset(
            str(tmp_path / "metadata.json"),
            engine="kerchunk",
            backend_kwargs={
                "storage_options": {
                    "remote_protocol": "https",
                    "remote_options": fs.storage_options,
                },
            },
        )

        xr.testing.assert_equal(result, expected)
