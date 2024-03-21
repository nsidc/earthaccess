from datetime import date, datetime, time, timedelta, timezone

import pytest
from dateutil.parser import ParserError
from earthaccess import search
from numpy import datetime64
from pandas import Timestamp

handled_dates = [
    ("", None),
    (None, None),
    ("2024", "2024-01-01T00:00:00Z"),
    ("2024-02", "2024-02-01T00:00:00Z"),
    ("2024-02-03T10", "2024-02-03T10:00:00Z"),
    ("2024-02-03T10:08:54", "2024-02-03T10:08:54Z"),
    ("2024-02-03T10:08:54Z", "2024-02-03T10:08:54Z"),
    ("2024-02-03T10:08:54+00:00", "2024-02-03T10:08:54Z"),
    ("2024-02-03T10:08:54-09:00", "2024-02-03T19:08:54Z"),
    (date(1985, 10, 19), "1985-10-19T00:00:00Z"),
    (datetime(1985, 10, 19, 12), "1985-10-19T12:00:00Z"),
    (datetime(1985, 10, 19, 12, 24), "1985-10-19T12:24:00Z"),
    (datetime(1985, 10, 19, 12, 24, tzinfo=timezone.utc), "1985-10-19T12:24:00Z"),
    (
        datetime(1985, 10, 19, 12, 24, tzinfo=timezone(timedelta(hours=-9))),
        "1985-10-19T21:24:00Z",
    ),
    (Timestamp("1985-10-19"), "1985-10-19T00:00:00Z"),
    ("foobar", ParserError("Unknown string format: foobar")),
    (time(0, 0), TypeError("Dates must be a date object or str, not time.")),
    (
        datetime64(0, "ns"),
        TypeError("Dates must be a date object or str, not datetime64."),
    ),
    (Timestamp(""), ValueError("Provided date NaT is not valid.")),
]


@pytest.mark.parametrize("raw,expected", handled_dates)
def test__normalize_datetime(raw, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=str(expected)):
            _ = search._normalize_datetime(raw)
    elif expected:
        assert (
            search._normalize_datetime(raw).strftime("%Y-%m-%dT%H:%M:%SZ") == expected
        )
    else:
        assert search._normalize_datetime(raw) is None
