import unittest

import earthaccess
import vcr
from earthaccess.search import DataCollections

my_vcr = vcr.VCR(
    record_mode="once",
    decode_compressed_response=True,
    # Header matching is not set by default, we need that to test the
    # search-after functionality is performing correctly.
    match_on=["method", "scheme", "host", "port", "path", "query", "headers"],
)


def assert_unique_results(results):
    """
    When we invoke a search request multiple times we want to ensure that we don't
    get the same results back. This is a one shot test as the results are preserved
    by VCR but still useful.
    """
    concept_ids = []
    for result in results:
        concept_ids.append(result["meta"]["concept-id"])

    unique_concept_ids = set(concept_ids)
    return len(unique_concept_ids) == len(concept_ids)


class TestResults(unittest.TestCase):
    def test_data_links(self):
        with my_vcr.use_cassette(
            "tests/unit/fixtures/vcr_cassettes/SEA_SURFACE_HEIGHT_ALT_GRIDS_L4_2SATS_5DAY_6THDEG_V_JPL2205.yaml"
        ):
            granules = earthaccess.search_data(
                short_name="SEA_SURFACE_HEIGHT_ALT_GRIDS_L4_2SATS_5DAY_6THDEG_V_JPL2205",
                temporal=("2020", "2022"),
                count=1,
            )
            g = granules[0]
            # `access` specified
            assert g.data_links(access="direct")[0].startswith("s3://")
            assert g.data_links(access="external")[0].startswith("https://")
            # `in_region` specified
            assert g.data_links(in_region=True)[0].startswith("s3://")
            assert g.data_links(in_region=False)[0].startswith("https://")
            # When `access` and `in_region` are both specified, `access` takes priority
            assert g.data_links(access="direct", in_region=True)[0].startswith("s3://")
            assert g.data_links(access="direct", in_region=False)[0].startswith("s3://")
            assert g.data_links(access="external", in_region=True)[0].startswith(
                "https://"
            )
            assert g.data_links(access="external", in_region=False)[0].startswith(
                "https://"
            )

    def test_get_more_than_2000(self):
        """
        If we execute a get with a limit of more than 2000
        then we expect multiple invocations of a cmr granule search and
        to not fetch back more results than we ask for
        """
        with my_vcr.use_cassette(
            "tests/unit/fixtures/vcr_cassettes/MOD02QKM.yaml"
        ) as cass:
            granules = earthaccess.search_data(short_name="MOD02QKM", count=3000)

            self.assertEqual(len(granules), 3000)

            # Assert that we performed one 'hits' search and two 'results' search queries
            self.assertEqual(len(cass), 3)

            assert_unique_results(granules)

    def test_get(self):
        """
        If we execute a get with no arguments then we expect
        to get the maximum no. of granules from a single CMR call (2000)
        in a single request
        """
        with my_vcr.use_cassette(
            "tests/unit/fixtures/vcr_cassettes/MOD02QKM_2000.yaml"
        ) as cass:
            granules = earthaccess.search_data(short_name="MOD02QKM", count=2000)

            self.assertEqual(len(granules), 2000)

            # Assert that we performed one 'hits' search and one 'results' search queries
            self.assertEqual(len(cass), 2)

            assert_unique_results(granules)

    def test_get_all_less_than_2k(self):
        """
        If we execute a get_all then we expect multiple
        invocations of a cmr granule search and
        to not fetch back more results than we ask for
        """
        with my_vcr.use_cassette(
            "tests/unit/fixtures/vcr_cassettes/TELLUS_GRAC.yaml"
        ) as cass:
            granules = earthaccess.search_data(
                short_name="TELLUS_GRAC_L3_JPL_RL06_LND_v04", count=2000
            )

            self.assertEqual(len(granules), 163)

            # Assert that we performed a hits query and one search results query
            self.assertEqual(len(cass), 2)

            assert_unique_results(granules)

    def test_get_all_more_than_2k(self):
        """
        If we execute a get_all then we expect multiple
        invocations of a cmr granule search and
        to not fetch back more results than we ask for
        """
        with my_vcr.use_cassette(
            "tests/unit/fixtures/vcr_cassettes/CYGNSS.yaml"
        ) as cass:
            granules = earthaccess.search_data(
                short_name="CYGNSS_NOAA_L2_SWSP_25KM_V1.2", count=3000
            )

            self.assertEqual(len(granules), 2478)

            # Assert that we performed a hits query and two search results queries
            self.assertEqual(len(cass), 3)

            assert_unique_results(granules)

    def test_collections_less_than_2k(self):
        """
        If we execute a get_all then we expect multiple
        invocations of a cmr granule search and
        to not fetch back more results than we ask for
        """
        with my_vcr.use_cassette(
            "tests/unit/fixtures/vcr_cassettes/PODAAC.yaml"
        ) as cass:
            query = DataCollections().daac("PODAAC").cloud_hosted(True)
            collections = query.get(20)

            self.assertEqual(len(collections), 20)

            # Assert that we performed a single search results query
            self.assertEqual(len(cass), 1)

            assert_unique_results(collections)
            
            self.is_using_search_after(cass)

    def test_collections_more_than_2k(self):
        """
        If we execute a get_all then we expect multiple
        invocations of a cmr granule search and
        to not fetch back more results than we ask for
        """
        with my_vcr.use_cassette("tests/unit/fixtures/vcr_cassettes/ALL.yaml") as cass:
            query = DataCollections()
            collections = query.get(3000)

            self.assertEqual(len(collections), 3000)

            # Assert that we performed two search results queries
            self.assertEqual(len(cass), 2)

            assert_unique_results(collections)
            
            self.is_using_search_after(cass)

    def is_using_search_after(self, cass):
        # Verify the page no. was not used
        first_request = True
        for request in cass.requests:
            self.assertTrue('page_num' not in request.uri)
                # Verify that Search After was used in all requests except first               
            if first_request:
                self.assertFalse('CMR-Search-After' in request.headers)
            else:
                self.assertTrue('CMR-Search-After' in request.headers)
            first_request = False