# package imports
import json
import logging
import os
import unittest

import earthaccess
from earthaccess.api import search_datasets

assertions = unittest.TestCase("__init__")
logger = logging.getLogger(__name__)

assertions.assertTrue("EARTHDATA_USERNAME" in os.environ)
assertions.assertTrue("EARTHDATA_PASSWORD" in os.environ)

logger.info(f"Current username: {os.environ['EARTHDATA_USERNAME']}")
logger.info(f"earthaccess version: {earthaccess.__version__}")


def test_services():
    """Test that a list of services can be retrieved."""
    
    datasets = search_datasets(
        short_name = "MUR-JPL-L4-GLOB-v4.1",
        cloud_hosted= True,
        temporal = ("2024-02-27", "2024-02-29")
    )
    
    with open("tests/integration/test_data/test_services_MUR.json") as jf:
        expected_response = json.load(jf)
    
    dataset_services = {}
    for dataset in datasets:
        dataset_services[dataset["umm"]["ShortName"]] = dataset.services()
    actual_response = dataset_services
    assertions.assertTrue(expected_response == actual_response)
    