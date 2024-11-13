import logging
import os
from pathlib import Path
from unittest.mock import patch

import earthaccess
import pytest

logger = logging.getLogger(__name__)


dataset_valid_params = [
    {"data_center": "NSIDC", "cloud_hosted": True},
    {"keyword": "aerosol", "cloud_hosted": False},
    {"daac": "NSIDC", "keyword": "ocean"},
]

granules_valid_params = [
    {
        "data_center": "NSIDC",
        "short_name": "ATL08",
        "cloud_hosted": True,
        # Chiapas, Mexico
        "bounding_box": (-92.86, 16.26, -91.58, 16.97),
    },
    {
        "concept_id": "C2021957295-LPCLOUD",
        "day_night_flag": "day",
        "cloud_cover": (0, 20),
        # Southern Ireland
        "bounding_box": (-10.15, 51.61, -7.59, 52.43),
    },
]


def test_auth_returns_valid_auth_class():
    auth = earthaccess.login(strategy="environment")
    assert isinstance(auth, earthaccess.Auth)
    assert isinstance(earthaccess.__auth__, earthaccess.Auth)
    assert earthaccess.__auth__.authenticated


def test_dataset_search_returns_none_with_no_parameters():
    results = earthaccess.search_datasets()
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.parametrize("kwargs", dataset_valid_params)
def test_dataset_search_returns_valid_results(kwargs):
    results = earthaccess.search_datasets(**kwargs)
    assert isinstance(results, list)
    assert isinstance(results[0], dict)


@pytest.mark.parametrize("kwargs", granules_valid_params)
def test_granules_search_returns_valid_results(kwargs):
    results = earthaccess.search_data(count=10, **kwargs)
    assert isinstance(results, list)
    assert len(results) <= 10


@pytest.mark.parametrize("selection", [0, slice(None)])
@pytest.mark.parametrize("use_url", [True, False])
def test_download(tmp_path, selection, use_url):
    results = earthaccess.search_data(
        count=2,
        short_name="ATL08",
        cloud_hosted=True,
        bounding_box=(-92.86, 16.26, -91.58, 16.97),
    )
    if use_url:
        # Download via file URL string instead of DataGranule object
        results = [link for r in results for link in r.data_links(access="indirect")]
    result = results[selection]
    files = earthaccess.download(result, str(tmp_path))
    assert isinstance(files, list)
    assert all(Path(f).exists() for f in files)


def fail_to_download_file(*args, **kwargs):
    raise IOError("Download failed")


def test_download_immediate_failure(tmp_path: Path):
    results = earthaccess.search_data(
        short_name="ATL06",
        bounding_box=(-10, 20, 10, 50),
        temporal=("1999-02", "2019-03"),
        count=3,
    )

    with patch.object(earthaccess.__store__, "_download_file", fail_to_download_file):
        with pytest.raises(IOError, match="Download failed"):
            # By default, we set pqdm exception_behavior to "immediate" so that
            # it simply propagates the first download error it encounters, halting
            # any further downloads.
            earthaccess.download(results, tmp_path, pqdm_kwargs=dict(disable=True))


def test_download_deferred_failure(tmp_path: Path):
    count = 3
    results = earthaccess.search_data(
        short_name="ATL06",
        bounding_box=(-10, 20, 10, 50),
        temporal=("1999-02", "2019-03"),
        count=count,
    )

    with patch.object(earthaccess.__store__, "_download_file", fail_to_download_file):
        # With "deferred" exceptions, pqdm catches all exceptions, then at the end
        # raises a single generic Exception, passing the sequence of caught exceptions
        # as arguments to the Exception constructor.
        with pytest.raises(Exception) as exc_info:
            earthaccess.download(
                results,
                tmp_path,
                pqdm_kwargs=dict(exception_behaviour="deferred", disable=True),
            )

    errors = exc_info.value.args
    assert len(errors) == count
    assert all(isinstance(e, IOError) and str(e) == "Download failed" for e in errors)


def test_auth_environ():
    earthaccess.login(strategy="environment")
    environ = earthaccess.auth_environ()
    assert environ == {
        "EARTHDATA_USERNAME": os.environ["EARTHDATA_USERNAME"],
        "EARTHDATA_PASSWORD": os.environ["EARTHDATA_PASSWORD"],
    }


def test_auth_environ_raises(monkeypatch):
    # Ensure `earthaccess.__auth__` always returns a new,
    # unauthenticated `earthaccess.Auth` instance, bypassing
    # automatic auth behavior
    monkeypatch.setattr(earthaccess, "__auth__", earthaccess.Auth())

    # Ensure `earthaccess.auth_environ()` raises an informative error
    # when not authenticated
    with pytest.raises(RuntimeError, match="authenticate"):
        earthaccess.auth_environ()
