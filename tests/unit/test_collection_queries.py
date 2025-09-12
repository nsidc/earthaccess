# package imports
import datetime as dt

import pytest
from earthaccess.search import DataCollections

valid_single_dates = [
    ("2001-12-12", "2001-12-21", "2001-12-12T00:00:00Z,2001-12-21T23:59:59Z"),
    ("2021-02-01", "", "2021-02-01T00:00:00Z,"),
    ("1999-02-01 06:00", "2009-01-01", "1999-02-01T06:00:00Z,2009-01-01T23:59:59Z"),
    (
        dt.datetime(2021, 2, 1),
        dt.datetime(2021, 2, 2),
        "2021-02-01T00:00:00Z,2021-02-02T00:00:00Z",
    ),
    (
        "2019-03-10T00:00:00Z",
        "2019-03-11T23:59:59Z",
        "2019-03-10T00:00:00Z,2019-03-11T23:59:59Z",
    ),
    (
        "2019-03-10T00:00:00Z",
        "2019-03-10T00:00:00-01:00",
        "2019-03-10T00:00:00Z,2019-03-10T01:00:00Z",
    ),
]

invalid_single_dates = [
    ("2001-12-45", "2001-12-21", None),
    ("2021w1", "", None),
    ("2999-02-01", "2009-01-01", None),
]


def test_no_default_params():
    query = DataCollections()
    assert len(query.params) == 0


def test_query_can_find_cloud_provider():
    query = DataCollections().daac("PODAAC").cloud_hosted(True)
    assert query.params["provider"] == "POCLOUD"
    query = DataCollections().cloud_hosted(True).daac("PODAAC")
    assert query.params["provider"] == "POCLOUD"
    # SEDAC does not have a cloud provider, so it should default to the on prem provider
    query = DataCollections().cloud_hosted(True).daac("SEDAC")
    assert query.params["provider"] == "ESDIS"
    query = DataCollections().daac("ASDC").cloud_hosted(True)
    assert query.params["provider"] == "LARC_CLOUD"
    query = DataCollections().cloud_hosted(True).daac("ASDC")
    assert query.params["provider"] == "LARC_CLOUD"


def test_querybuilder_can_handle_doi():
    doi = "10.5067/AQR50-3Q7CS"
    query = DataCollections().doi(doi)
    assert query.params["doi"] == doi
    query = DataCollections().cloud_hosted(True).daac("PODAAC").doi(doi)
    assert query.params["doi"] == doi


def test_querybuilder_can_handle_has_granules():
    query = DataCollections().has_granules(False)
    assert not query.params["has_granules"]
    query = DataCollections().has_granules(True)
    assert query.params["has_granules"]
    query = DataCollections().has_granules(None)
    assert "has_granules" not in query.params


@pytest.mark.parametrize("start,end,expected", valid_single_dates)
def test_query_can_parse_single_dates(start, end, expected):
    query = DataCollections().temporal(start, end)
    assert query.params["temporal"][0] == expected


@pytest.mark.parametrize("start,end,expected", invalid_single_dates)
def test_query_can_handle_invalid_dates(start, end, expected):
    query = DataCollections()
    try:
        query = query.temporal(start, end)
    except Exception as e:
        assert isinstance(e, ValueError)
        assert "temporal" not in query.params
