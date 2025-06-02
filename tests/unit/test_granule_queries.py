# package imports
import datetime as dt

import pytest
from earthaccess.search import DataGranules

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

bbox_queries = [
    ([-134.7, 54.9, -100.9, 69.2], True),
    ([-10, 20, 0, 40], True),
    ([10, 20, 30, 40], True),
]

point_queries = [
    ([-134.7, 54.9], True),
    ([-10, 20], True),
    ([30, 40], True),
]

line_queries = [
    ([-134.7, 54.9, -100.9, 69.2], True),
    ([-10, 20, 0, 40], True),
    ([10, 20, 30, 40], True),
]

polygon_queries = [
    ([-134.7, 54.9, -100.9, 54.9, -100.9, 69.2, -134.7, 69.2, -134.7, 54.9], True),
    ([-10, 20, 0, 20, 0, 40, -10, 40, -10, 20], True),
]


@pytest.mark.parametrize("start,end,expected", valid_single_dates)
def test_query_can_parse_single_dates(start, end, expected):
    granules = DataGranules().short_name("MODIS").temporal(start, end)
    assert granules.params["temporal"][0] == expected
    granules = DataGranules().short_name("MODIS").revision_date(start, end)
    assert granules.params["revision_date"][0] == expected
    granules = DataGranules().short_name("MODIS").created_at(start, end)
    assert granules.params["created_at"][0] == expected
    granules = DataGranules().short_name("MODIS").production_date(start, end)
    assert granules.params["production_date"][0] == expected


@pytest.mark.parametrize("start,end,expected", invalid_single_dates)
def test_query_can_handle_invalid_dates(start, end, expected):
    granules = DataGranules().short_name("MODIS")
    try:
        granules = granules.temporal(start, end)
    except Exception as e:
        assert isinstance(e, ValueError)
        assert "temporal" not in granules.params
    try:
        granules = granules.revision_date(start, end)
    except Exception as e:
        assert isinstance(e, ValueError)
        assert "revision_date" not in granules.params
    try:
        granules = granules.created_at(start, end)
    except Exception as e:
        assert isinstance(e, ValueError)
        assert "created_at" not in granules.params
    try:
        granules = granules.production_date(start, end)
    except Exception as e:
        assert isinstance(e, ValueError)
        assert "production_date" not in granules.params


@pytest.mark.parametrize("bbox,expected", bbox_queries)
def test_query_handles_bbox(bbox, expected):
    granules = DataGranules().short_name("MODIS").bounding_box(*bbox)
    assert ("bounding_box" in granules.params) == expected


@pytest.mark.parametrize("point,expected", point_queries)
def test_query_handles_point(point, expected):
    granules = DataGranules().short_name("MODIS").point(point)
    assert ("point" in granules.params) == expected


@pytest.mark.parametrize("line,expected", line_queries)
def test_query_handles_line(line, expected):
    granules = DataGranules().short_name("MODIS").line(line)
    assert ("line" in granules.params) == expected


@pytest.mark.parametrize("polygon,expected", polygon_queries)
def test_query_handles_polygon(polygon, expected):
    granules = DataGranules().short_name("MODIS").polygon(polygon)
    assert ("polygon" in granules.params) == expected
