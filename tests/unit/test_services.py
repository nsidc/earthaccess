import unittest

import earthaccess
from earthaccess.api import search_datasets
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

    def _get_vcr_kwargs(self, **kwargs):
        kwargs["decode_compressed_response"] = True
        return kwargs

    def _get_vcr(self, **kwargs):
        myvcr = super(TestServices, self)._get_vcr(
            filter_headers=["Authorization"],
            filter_post_data_parameters=["access_token"],
            before_record_response=self.scrub_access_token("access_token", "token"),
        )
        myvcr.cassette_library_dir = "tests/unit/fixtures/vcr_cassettes"
        return myvcr

    def test_services(self):
        """Test DataService get function return of service metadata results."""
        earthaccess._auth.authenticated = False
        query = earthaccess.services.DataService().parameters(
            concept_id="S2004184019-POCLOUD"
        )
        actual = query.get(query.hits())

        self.assertTrue(actual[0]["umm"]["Type"] == "OPeNDAP")
        self.assertTrue(
            actual[0]["umm"]["ServiceOrganizations"][0]["ShortName"] == "UCAR/UNIDATA"
        )
        self.assertTrue(
            actual[0]["umm"]["Description"] == "Earthdata OPEnDAP in the cloud"
        )
        self.assertTrue(actual[0]["umm"]["LongName"] == "PO.DAAC OPeNDADP In the Cloud")

    def test_service_results(self):
        """Test results.DataCollection.services to return available services."""
        datasets = search_datasets(
            short_name="MUR-JPL-L4-GLOB-v4.1",
            cloud_hosted=True,
            temporal=("2024-02-27T00:00:00Z", "2024-02-29T00:00:00Z"),
        )
        earthaccess._auth.authenticated = False
        results = datasets[0].services()

        self.assertTrue(
            results["S2004184019-POCLOUD"][0]["meta"]["provider-id"] == "POCLOUD"
        )
        self.assertTrue(
            results["S2004184019-POCLOUD"][0]["umm"]["URL"]["URLValue"]
            == "https://opendap.earthdata.nasa.gov/"
        )
        self.assertTrue(
            results["S2606110201-XYZ_PROV"][0]["umm"]["Name"] == "Harmony GDAL Adapter (HGA)"
        )
        self.assertTrue(results["S2164732315-XYZ_PROV"][0]["umm"]["Type"] == "Harmony")


if __name__ == "__main__":
    unittest.main()
