import logging
import unittest

import earthaccess
import pytest
from virtualizarr.manifests.array import ManifestArray

logger = logging.getLogger(__name__)
assertions = unittest.TestCase("__init__")


auth = earthaccess.login()
logger.info(
    "earthaccess version: %s, authenticated: %s",
    earthaccess.__version__,
    auth.authenticated,
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
    return earthaccess.search_data(
        count=count,
        temporal=("2025"),
        short_name=short_name,
    )


def test_virtualize_materialize_indexable(granules):
    # Simply check that the dmrpp can be found, parsed, and loaded. Actual parser result is checked in virtualizarr
    vds = earthaccess.virtualize(
        granules,
        concat_dim="time",
        load=True,
        access="indirect",
    )
    # We can use fancy indexing
    assert vds.isel(time=0) is not None


def test_virtualize_non_materialize(granules):
    # Simply check that the dmrpp can be found, parsed, and loaded. Actual parser result is checked in virtualizarr
    vds = earthaccess.virtualize(
        granules,
        concat_dim="time",
        load=False,
        access="indirect",
    )
    # we are not materializing the data
    for name in vds.data_vars:
        assert isinstance(vds[name].variable.data, ManifestArray)


MUR_COLLECTION_CONCEPT_ID = "C1996881146-POCLOUD"
MUR_VIRTUAL_URL = (
    "https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-docs/ghrsst/open/"
    "docs/MUR-JPL-L4-GLOB-v4.1_combined-ref.json"
)


def test_open_virtual_from_collection():
    """open_virtual(DataCollection) opens the MUR virtual store via HTTPS."""
    collection = earthaccess.search_datasets(
        count=1, concept_id=MUR_COLLECTION_CONCEPT_ID
    )[0]
    vds = earthaccess.open_virtual(collection, access="indirect", force_external=True)
    assert vds is not None
    assert len(vds.dims) > 0


def test_open_virtual_from_url():
    """open_virtual(str) opens the MUR virtual store URL via kerchunk engine."""
    vds = earthaccess.open_virtual(MUR_VIRTUAL_URL, force_external=True)
    assert vds is not None
    assert len(vds.dims) > 0


def test_open_virtual_load_false_from_collection():
    """open_virtual(collection, load=False) returns a virtual dataset with ManifestArrays."""
    from virtualizarr.manifests.array import ManifestArray

    collection = earthaccess.search_datasets(
        count=1, concept_id=MUR_COLLECTION_CONCEPT_ID
    )[0]
    vds = earthaccess.open_virtual(
        collection, load=False, access="indirect", force_external=True
    )
    assert vds is not None
    assert len(vds.dims) > 0
    for name in vds.data_vars:
        assert isinstance(vds[name].variable.data, ManifestArray)


def test_open_virtual_load_false_external_url():
    """open_virtual(external URL, load=False) reads a public kerchunk reference."""
    from virtualizarr.manifests.array import ManifestArray

    external_url = (
        "https://its-live-data.s3-us-west-2.amazonaws.com/test-space/vds/"
        "SPL4SMGP.parquet"
    )
    vds = earthaccess.open_virtual(external_url, load=False)
    assert vds is not None
    assert len(vds.dims) > 0
    for name in vds.data_vars:
        assert isinstance(vds[name].variable.data, ManifestArray)
