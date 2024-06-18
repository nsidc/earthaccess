import logging
import os
import unittest

import earthaccess
import pytest

pytest.importorskip("virtualizarr")
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
        short_name="MUR-JPL-L4-GLOB-v4.1",
        cloud_hosted=True
    )
    return granules


@pytest.mark.parametrize("output", "memory")
def test_open_virtual_mfdataset(tmp_path, granules, output):
    xr = pytest.importorskip("xarray")
    # Open directly with `earthaccess.open`
    expected = xr.open_mfdataset(earthaccess.open(granules), concat_dim="time", combine="nested", combine_attrs="drop_conflicts")

    result = earthaccess.open_virtual_mfdataset(granules=granules, access="indirect", concat_dime="time",  parallel=True, preprocess=None)
    # dimensions
    assert result.sizes == expected.sizes
    # variable names, variable dimensions
    assert result.variables.keys() == expected.variables.keys()
    # attributes
    assert result.attrs == expected.attrs
    # coordinates
    assert result.coords.keys() == expected.coords.keys()
    # chunks
    assert result.chunks == expected.chunks
    # encoding
    assert result.encoding == expected.encoding
