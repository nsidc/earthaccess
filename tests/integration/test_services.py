# package imports
import logging
import os
import unittest

import earthaccess
from earthaccess.api import search_datasets
from vcr.unittest import VCRTestCase  # type: ignore[import-untyped]

assertions = unittest.TestCase("__init__")
logger = logging.getLogger(__name__)

assertions.assertTrue("EARTHDATA_USERNAME" in os.environ)
assertions.assertTrue("EARTHDATA_PASSWORD" in os.environ)

logger.info(f"Current username: {os.environ['EARTHDATA_USERNAME']}")
logger.info(f"earthaccess version: {earthaccess.__version__}")


class TestServices(VCRTestCase):
    def scrub_access_token(self, string, replacement=""):
        def before_record_response(response):
            body_string = str(response["body"]["string"])
            if "access_token" in body_string:
                response["body"]["string"] = "ACCESS_TOKEN"
            if "uid" in body_string:
                response["body"]["string"] = "UID"
            return response

        return before_record_response

    def _get_vcr(self, **kwargs):
        myvcr = super(TestServices, self)._get_vcr(
            filter_headers=["Authorization"],
            filter_post_data_parameters=["access_token"],
            before_record_response=self.scrub_access_token("access_token", "token"),
        )
        myvcr.cassette_library_dir = "tests/integration/fixtures/vcr_cassettes"
        return myvcr

    def test_services(self):
        """Test that a list of services can be retrieved."""

        datasets = search_datasets(
            short_name="MUR-JPL-L4-GLOB-v4.1",
            cloud_hosted=True,
            temporal=("2024-02-27T00:00:00Z", "2024-02-29T00:00:00Z"),
        )

        dataset_services = {}
        for dataset in datasets:
            dataset_services[dataset["umm"]["ShortName"]] = dataset.services()
        actual_response = dataset_services

        self.assertEqual(list(actual_response.keys())[0], "MUR-JPL-L4-GLOB-v4.1")
        self.assertEqual(
            actual_response["MUR-JPL-L4-GLOB-v4.1"]["S2606110201-XYZ_PROV"][0]["umm"][
                "LongName"
            ],
            "Harmony GDAL Adapter (HGA)",
        )
        self.assertEqual(
            actual_response["MUR-JPL-L4-GLOB-v4.1"]["S2839491596-XYZ_PROV"][0]["umm"][
                "URL"
            ]["Description"],
            "https://harmony.earthdata.nasa.gov",
        )
