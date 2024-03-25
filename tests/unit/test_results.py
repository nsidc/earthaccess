import json
import unittest

import earthaccess


assertions = unittest.TestCase("__init__")


def test_data_links():
    granules = earthaccess.search_data(
        short_name="SEA_SURFACE_HEIGHT_ALT_GRIDS_L4_2SATS_5DAY_6THDEG_V_JPL2205",
        temporal=("2020", "2022"),
        count=1,
    )
    g = granules[0]
    # `access` specified
    assert g.data_links(access="direct")[0].startswith("s3://")
    assert g.data_links(access="external")[0].startswith("https://")
    # `in_region` specified
    assert g.data_links(in_region=True)[0].startswith("s3://")
    assert g.data_links(in_region=False)[0].startswith("https://")
    # When `access` and `in_region` are both specified, `access` takes priority
    assert g.data_links(access="direct", in_region=True)[0].startswith("s3://")
    assert g.data_links(access="direct", in_region=False)[0].startswith("s3://")
    assert g.data_links(access="external", in_region=True)[0].startswith("https://")
    assert g.data_links(access="external", in_region=False)[0].startswith("https://")


def test_services():
    """Test DataService get function return of service metadata results."""
    
    query = earthaccess.services.DataService().parameters(concept_id="S2004184019-POCLOUD")
    actual = query.get(query.hits())
    actual = json.loads(actual[0])
    with open("tests/unit/fixtures/S2004184019-POCLOUD.json") as jf:
        expected = json.load(jf)
    assertions.assertTrue(actual["items"] == expected[0]["items"])