import earthaccess
from vcr.unittest import VCRTestCase  # type: ignore[import-untyped]


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
        return super()._get_vcr(
            **kwargs,
            before_record_response=self.scrub_access_token("access_token", "token"),
            cassette_library_dir="tests/integration/fixtures/vcr_cassettes",
            decode_compressed_response=True,
            filter_headers=["Authorization"],
            filter_post_data_parameters=["access_token"],
        )

    def test_services(self):
        """Test that a list of services can be retrieved."""
        datasets = earthaccess.search_datasets(
            short_name="MUR-JPL-L4-GLOB-v4.1",
            cloud_hosted=True,
            temporal=("2024-02-27T00:00:00Z", "2024-02-29T00:00:00Z"),
        )

        dataset_services = {
            dataset["umm"]["ShortName"]: dataset.services() for dataset in datasets
        }

        self.assertEqual(list(dataset_services.keys())[0], "MUR-JPL-L4-GLOB-v4.1")
        self.assertEqual(
            dataset_services["MUR-JPL-L4-GLOB-v4.1"]["S2606110201-XYZ_PROV"][0]["umm"][
                "LongName"
            ],
            "Harmony GDAL Adapter (HGA)",
        )
        self.assertEqual(
            dataset_services["MUR-JPL-L4-GLOB-v4.1"]["S2839491596-XYZ_PROV"][0]["umm"][
                "URL"
            ]["Description"],
            "https://harmony.earthdata.nasa.gov",
        )
