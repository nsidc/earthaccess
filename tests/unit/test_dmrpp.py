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


@pytest.fixture(scope="module")
def granules():
    granules = earthaccess.search_data(
        count=2, temporal=("2024-08-01"), short_name="MUR25-JPL-L4-GLOB-v04.2"
    )
    return granules


def test_dmrpp(granules):
    xr = pytest.importorskip("xarray")
    virtualizarr = pytest.importorskip("virtualizarr")
    earthaccess = pytest.importorskip("earthaccess")
    fs = pytest.importorskip("fsspec")

    from earthaccess.dmrpp import DMRParser

    data_path = granules[0].data_links(access="indirect")[0]
    dmrpp_path = data_path + ".dmrpp"

    fs = earthaccess.get_fsspec_https_session()
    with fs.open(dmrpp_path) as f:
        parser = DMRParser(f.read(), data_filepath=data_path)
    result = parser.parse_dataset()

    from virtualizarr import open_virtual_dataset

    expected = open_virtual_dataset(
        data_path, indexes={}, reader_options={"storage_options": fs.storage_options}
    )

    xr.testing.assert_identical(result, expected)
