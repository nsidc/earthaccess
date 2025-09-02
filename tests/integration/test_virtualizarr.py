import logging
import os
import unittest

import earthaccess
import pytest

logger = logging.getLogger(__name__)
assertions = unittest.TestCase("__init__")

assertions.assertTrue("EARTHDATA_USERNAME" in os.environ)
assertions.assertTrue("EARTHDATA_PASSWORD" in os.environ)

logger.info(f"Current username: {os.environ['EARTHDATA_USERNAME']}")
logger.info(f"earthaccess version: {earthaccess.__version__}")


@pytest.fixture(
    scope="module",
    params=[
        ("MUR25-JPL-L4-GLOB-v04.2", 2),
        ("AVHRR_OI-NCEI-L4-GLOB-v2.1", 1),
        ("M2T1NXSLV", 1),
    ],
)
def granules(request):
    short_name, count = request.param
    granules = earthaccess.search_data(
        count=count, temporal=("2024"), short_name=short_name
    )
    return granules


def test_open_virtual_dataset(granules):
    # Simply check that the dmrpp can be found, parsed, and loaded. Actual parser result is checked in virtualizarr
    vds = earthaccess.open_virtual_mfdataset(granules, concat_dim="time")
    # We can use fancy indexing
    assert vds.isel(time=0) is not None
