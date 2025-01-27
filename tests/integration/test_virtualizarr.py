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
        "MUR25-JPL-L4-GLOB-v04.2",
        "AVHRR_OI-NCEI-L4-GLOB-v2.1",
        "M2T1NXSLV",
    ],
)
def granule(request):
    granules = earthaccess.search_data(
        count=1, temporal=("2024"), short_name=request.param
    )
    return granules[0]


def test_open_virtual_dataset(granule):
    # Simply check that the dmrpp can be found, parsed, and loaded. Actual parser result is checked in virtualizarr
    vds = earthaccess.open_virtual_dataset(granule, load=False)
    assert vds is not None
    vds_load = earthaccess.open_virtual_dataset(granule, load=True)
    assert vds_load is not None
