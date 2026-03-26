import logging
import unittest

import earthaccess
import pytest

logger = logging.getLogger(__name__)
assertions = unittest.TestCase("__init__")


auth = earthaccess.login()
logger.info(
    f"earthaccess version: {earthaccess.__version__}, authenticated: {auth.authenticated}"
)


@pytest.fixture(
    scope="module",
    params=[
        ("MUR25-JPL-L4-GLOB-v04.2", 2),
        ("AVHRR_OI-NCEI-L4-GLOB-v2.1", 1),
        ("TEMPO_NO2_L3", 2),
        ("M2T1NXSLV", 1),
    ],
)
def granules(request):
    short_name, count = request.param
    granules = earthaccess.search_data(
        count=count, temporal=("2025"), short_name=short_name
    )
    return granules


def test_virtualize_materialize_indexable(granules):
    # Simply check that the dmrpp can be found, parsed, and loaded. Actual parser result is checked in virtualizarr
    vds = earthaccess.virtualize(
        granules, concat_dim="time", load=True, access="indirect"
    )
    # We can use fancy indexing
    assert vds.isel(time=0) is not None


def test_virtualize_non_materialize(granules):
    from virtualizarr.manifests.array import ManifestArray

    # Simply check that the dmrpp can be found, parsed, and loaded. Actual parser result is checked in virtualizarr
    vds = earthaccess.virtualize(
        granules, concat_dim="time", load=False, access="indirect"
    )
    # we are not materializing the data
    for name in vds.data_vars:
        assert isinstance(vds[name].variable.data, ManifestArray)
