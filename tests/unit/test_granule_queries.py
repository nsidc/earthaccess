# package imports
import datetime as dt

import pytest
from earthaccess.search import DataGranules

valid_single_dates = [
    ("2001-12-12", "2001-12-21", "2001-12-12T00:00:00Z,2001-12-21T00:00:00Z"),
    ("2021-02-01", "", "2021-02-01T00:00:00Z,"),
    ("1999-02-01 06:00", "2009-01-01", "1999-02-01T06:00:00Z,2009-01-01T00:00:00Z"),
    (
        dt.datetime(2021, 2, 1),
        dt.datetime(2021, 2, 2),
        "2021-02-01T00:00:00Z,2021-02-02T00:00:00Z",
    ),
    ("1999-02-01 06:00:00Z", "2009-01-01", "1999-02-01T06:00:00Z,2009-01-01T00:00:00Z"),
]

invalid_single_dates = [
    ("2001-12-45", "2001-12-21", ValueError),
    ("2021w1", "", ValueError),
    ("2999-02-01", "2009-01-01", ValueError),
    (123, "2009-01-01", TypeError),
]


bbox_queries = [
    ([-134.7, 54.9, -100.9, 69.2], True),
    ([-10, 20, 0, 40], True),
    ([10, 20, 30, 40], True),
]


@pytest.mark.parametrize("start,end,expected", valid_single_dates)
def test_query_can_parse_single_dates(start, end, expected):
    granules = DataGranules().short_name("MODIS").temporal(start, end)
    assert granules.params["temporal"][0] == expected


@pytest.mark.parametrize("start,end,exception", invalid_single_dates)
def test_query_can_handle_invalid_dates(start, end, exception):
    granules = DataGranules().short_name("MODIS")
    with pytest.raises(exception):
        granules = granules.temporal(start, end)
    assert "temporal" not in granules.params


@pytest.mark.parametrize("bbox,expected", bbox_queries)
def test_query_handles_bbox(bbox, expected):
    granules = DataGranules().short_name("MODIS").bounding_box(*bbox)
    assert ("bounding_box" in granules.params) == expected
