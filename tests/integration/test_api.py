# package imports
import logging
import os
import unittest

import earthaccess
import pytest
import responses

logger = logging.getLogger(__name__)
assertions = unittest.TestCase("__init__")

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


@responses.activate
def test_auth_returns_valid_auth_class():
    os.environ["EDL_USERNAME"] = "user"
    os.environ["EDL_PASSWORD"] = "password"

    json_response = [
        {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"},
        {"access_token": "EDL-token-2", "expiration_date": "12/16/2021"},
    ]
    responses.add(
        responses.GET,
        "https://urs.earthdata.nasa.gov/api/users/tokens",
        json=json_response,
        status=200,
    )

    auth = earthaccess.login(strategy="environment")
    assertions.assertIsInstance(auth, earthaccess.Auth)
    assertions.assertIsInstance(earthaccess.__auth__, earthaccess.Auth)
    assertions.assertTrue(earthaccess.__auth__.authenticated)


def test_dataset_search_returns_none_with_no_parameters():
    results = earthaccess.search_datasets()
    assertions.assertIsNone(results)


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
