import logging
import os
from pathlib import Path

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


def test_auth_returns_valid_auth_class(mock_env):
    auth = earthaccess.login(strategy="environment")
    assert isinstance(auth, earthaccess.Auth)
    assert isinstance(earthaccess.__auth__, earthaccess.Auth)
    assert earthaccess.__auth__.authenticated


def test_dataset_search_returns_none_with_no_parameters(mock_env):
    results = earthaccess.search_datasets()
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.parametrize("kwargs", dataset_valid_params)
def test_dataset_search_returns_valid_results(mock_env, kwargs):
    results = earthaccess.search_datasets(**kwargs)
    assert isinstance(results, list)
    assert isinstance(results[0], dict)


@pytest.mark.parametrize("kwargs", granules_valid_params)
def test_granules_search_returns_valid_results(mock_env, kwargs):
    results = earthaccess.search_data(count=10, **kwargs)
    assert isinstance(results, list)
    assert len(results) <= 10


@pytest.mark.parametrize("selection", [0, slice(None)])
@pytest.mark.parametrize("use_url", [True, False])
def test_download(mock_env, tmp_path, selection, use_url):
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


def test_auth_environ(mock_env):
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
