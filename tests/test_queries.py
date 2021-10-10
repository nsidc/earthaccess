# package imports
from datetime import datetime

import pytest
from earthdata.search import DataCollections, DataGranules

valid_single_dates = [
    ("2001-12-12", "2001-12-21", "2001-12-12T00:00:00Z,2001-12-21T00:00:00Z"),
    ("2021-02-01", "", "2021-02-01T00:00:00Z,"),
    ("1999-02-01 06:00", "2009-01-01", "1999-02-01T06:00:00Z,2009-01-01T00:00:00Z"),
]

invalid_single_dates = [
    ("2001-12-45", "2001-12-21", None),
    ("2021w1", "", None),
    ("2999-02-01", "2009-01-01", None),
]


@pytest.mark.parametrize("start,end,expected", valid_single_dates)
def test_query_can_parse_single_dates(start, end, expected):
    granules = DataGranules().short_name("MODIS").temporal(start, end)
    assert granules.params["temporal"][0] == expected


@pytest.mark.parametrize("start,end,expected", invalid_single_dates)
def test_query_can_handle_invalid_dates(start, end, expected):
    granules = DataGranules().short_name("MODIS")
    try:
        granules = granules.temporal(start, end)
    except Exception as e:
        assert isinstance(e, ValueError)
        assert "termporal" not in granules.params
