from datetime import date, datetime, time, timedelta, timezone

import pytest
from dateutil.parser import ParserError
from earthaccess import search


def test__normalize_datetime():
    normalized = search._normalize_datetime("")
    assert normalized is None

    normalized = search._normalize_datetime(None)
    assert normalized is None

    raw = "foobar"
    with pytest.raises(ParserError, match="Unknown string format: foobar"):
        _ = search._normalize_datetime(raw)

    raw = "2024"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    raw = "2023-02"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2023, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

    raw = "20210203"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2021, 2, 3, 0, 0, 0, tzinfo=timezone.utc)

    raw = "20240203T12"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2024, 2, 3, 12, 0, 0, tzinfo=timezone.utc)

    raw = "20240203T12:06"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2024, 2, 3, 12, 6, 0, tzinfo=timezone.utc)

    raw = "20240203T10:08:54"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2024, 2, 3, 10, 8, 54, tzinfo=timezone.utc)

    raw = "20240203T10:08:54Z"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2024, 2, 3, 10, 8, 54, tzinfo=timezone.utc)

    raw = "20240203T10:08:54+00:00"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2024, 2, 3, 10, 8, 54, tzinfo=timezone.utc)

    raw = "20240203T10:08:54-09:00"
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(2024, 2, 3, 19, 8, 54, tzinfo=timezone.utc)

    raw = date(1985, 10, 19)
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(1985, 10, 19, 0, 0, 0, tzinfo=timezone.utc)

    raw = datetime(1985, 10, 19)
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(1985, 10, 19, 0, 0, 0, tzinfo=timezone.utc)

    raw = datetime(1985, 10, 19, 12)
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(1985, 10, 19, 12, 0, 0, tzinfo=timezone.utc)

    raw = datetime(1985, 10, 19, 12, 24)
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(1985, 10, 19, 12, 24, 0, tzinfo=timezone.utc)

    raw = datetime(1985, 10, 19, 12, tzinfo=timezone.utc)
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(1985, 10, 19, 12, 0, 0, tzinfo=timezone.utc)

    raw = datetime(1985, 10, 19, 12, tzinfo=timezone(timedelta(hours=-9)))
    normalized = search._normalize_datetime(raw)
    assert normalized == datetime(1985, 10, 19, 21, 0, 0, tzinfo=timezone.utc)

    raw = time(12, 0)
    with pytest.raises(
        TypeError, match="Dates must be date, datetime, or str objects, not"
    ):
        _ = search._normalize_datetime(raw)
