from unittest.mock import Mock

import earthaccess
import pytest


def test_download(monkeypatch):
    earthaccess.login()

    results = earthaccess.search_data(
        short_name="ATL06",
        bounding_box=(-10, 20, 10, 50),
        temporal=("1999-02", "2019-03"),
        count=10,
    )

    def mock_get(*args, **kwargs):
        raise Exception("Download failed")

    mock_store = Mock()
    monkeypatch.setattr(earthaccess, "__store__", mock_store)
    monkeypatch.setattr(mock_store, "get", mock_get)

    with pytest.raises(Exception, match="Download failed"):
        earthaccess.download(results, "/home/download-folder")


def test_download_deferred_failure(monkeypatch):
    earthaccess.login()

    results = earthaccess.search_data(
        short_name="ATL06",
        bounding_box=(-10, 20, 10, 50),
        temporal=("1999-02", "2019-03"),
        count=10,
    )

    def mock_get(*args, **kwargs):
        return [Exception("Download failed")] * len(results)

    mock_store = Mock()
    monkeypatch.setattr(earthaccess, "__store__", mock_store)
    monkeypatch.setattr(mock_store, "get", mock_get)

    results = earthaccess.download(
        results, "/home/download-folder", None, 8, {"exception_behavior": "deferred"}
    )

    assert all(isinstance(e, Exception) for e in results)
    assert len(results) == 10
