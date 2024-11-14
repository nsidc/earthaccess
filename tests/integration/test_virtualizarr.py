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
    scope="module", params=["MUR25-JPL-L4-GLOB-v04.2"]
)
def granule(request):
    granules = earthaccess.search_data(
        count=1, temporal=("2024"), short_name=request.param
    )
    return granules[0]


def test_dmrpp(granule):
    from virtualizarr import open_virtual_dataset

    fs = earthaccess.get_fsspec_https_session()
    data_path = granule.data_links(access="indirect")[0]
    dmrpp_path = data_path + ".dmrpp"

    result = open_virtual_dataset(
        dmrpp_path,
        filetype="dmrpp",  # type: ignore
        indexes={},
        reader_options={"storage_options": fs.storage_options},  # type: ignore
    )

    expected = open_virtual_dataset(
        data_path,
        indexes={},
        reader_options={"storage_options": fs.storage_options},  # type: ignore
    )

    # TODO: replace with xr.testing when virtualizarr fill_val is fixed (https://github.com/zarr-developers/VirtualiZarr/issues/287)
    # and dmrpp deflateLevel (zlib compression level) is always present (https://github.com/OPENDAP/bes/issues/954)
    for var in result.variables:
        assert var in expected.variables
        assert result[var].dims == expected[var].dims
        assert result[var].shape == expected[var].shape
        assert result[var].dtype == expected[var].dtype
        assert result[var].data.manifest == expected[var].data.manifest
    assert set(result.coords) == set(expected.coords)
    assert result.attrs == expected.attrs
