import logging
import os
import unittest

import earthaccess
import pytest
from fsspec.core import strip_protocol

kerchunk = pytest.importorskip("kerchunk")
pytest.importorskip("dask")

logger = logging.getLogger(__name__)
assertions = unittest.TestCase("__init__")

assertions.assertTrue("EARTHDATA_USERNAME" in os.environ)
assertions.assertTrue("EARTHDATA_PASSWORD" in os.environ)

logger.info(f"Current username: {os.environ['EARTHDATA_USERNAME']}")
logger.info(f"earthaccess version: {earthaccess.__version__}")


@pytest.fixture(scope="module")
def granules():
    granules = earthaccess.search_data(
        count=2,
        short_name="SEA_SURFACE_HEIGHT_ALT_GRIDS_L4_2SATS_5DAY_6THDEG_V_JPL2205",
        cloud_hosted=True,
    )
    return granules


@pytest.mark.parametrize("protocol", ["", "file://"])
def test_consolidate_metadata_outfile(tmp_path, granules, protocol):
    outfile = f"{protocol}{tmp_path / 'metadata.json'}"
    assert not os.path.exists(outfile)
    result = earthaccess.consolidate_metadata(
        granules,
        outfile=outfile,
        access="indirect",
        kerchunk_options={"concat_dims": "Time"},
    )
    assert os.path.exists(strip_protocol(outfile))
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
