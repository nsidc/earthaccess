# package imports
import logging
import os
import shutil
import unittest

import earthaccess
import pytest

logger = logging.getLogger(__name__)
assertions = unittest.TestCase("__init__")


assertions.assertTrue("EARTHDATA_USERNAME" in os.environ)
assertions.assertTrue("EARTHDATA_PASSWORD" in os.environ)

logger.info(f"Current username: {os.environ['EARTHDATA_USERNAME']}")
logger.info(f"earthaccess version: {earthaccess.__version__}")


dataset_valid_params = [
    {"data_center": "NSIDC", "cloud_hosted": True},
    {"keyword": "aerosol", "cloud_hosted": False},
    {"daac": "PODAAC", "keyword": "ocean"},
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
    assertions.assertIsInstance(auth, earthaccess.Auth)
    assertions.assertIsInstance(earthaccess.__auth__, earthaccess.Auth)
    assertions.assertTrue(earthaccess.__auth__.authenticated)


def test_dataset_search_returns_none_with_no_parameters():
    results = earthaccess.search_datasets()
    assertions.assertIsInstance(results, list)
    assertions.assertTrue(len(results) == 0)


@pytest.mark.parametrize("kwargs", dataset_valid_params)
def test_dataset_search_returns_valid_results(kwargs):
    results = earthaccess.search_datasets(**kwargs)
    assertions.assertIsInstance(results, list)
    assertions.assertIsInstance(results[0], dict)


@pytest.mark.parametrize("kwargs", granules_valid_params)
def test_granules_search_returns_valid_results(kwargs):
    results = earthaccess.search_data(count=10, **kwargs)
    assertions.assertIsInstance(results, list)
    assertions.assertTrue(len(results) <= 10)


def test_earthaccess_api_can_download_granules():
    results = earthaccess.search_data(
        count=2,
        short_name="ATL08",
        cloud_hosted=True,
        bounding_box=(-92.86, 16.26, -91.58, 16.97),
    )
    local_path = "./tests/integration/data/ATL08"
    assertions.assertIsInstance(results, list)
    assertions.assertTrue(len(results) <= 2)
    files = earthaccess.download(results, local_path=local_path)
    assertions.assertIsInstance(files, list)
    shutil.rmtree(local_path)
