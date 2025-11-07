import contextlib
import json
import logging
import os.path

import earthaccess
import responses
from earthaccess.results import DataCollection
from earthaccess.search import DataCollections
from vcr.unittest import VCRTestCase  # type: ignore[import-untyped]

logging.basicConfig()
logging.getLogger("vcr").setLevel(logging.ERROR)

REDACTED_STRING = "REDACTED"


def unique_results(results):
    """When we invoke a search request multiple times we want to ensure that we don't
    get the same results back. This is a one shot test as the results are preserved
    by VCR but still useful.
    """
    unique_concept_ids = {result["meta"]["concept-id"] for result in results}
    return len(unique_concept_ids) == len(results)


def redact_login_request(request):
    if "/api/users/" in request.path and "/api/users/tokens" not in request.path:
        _, user_name = os.path.split(request.path)
        request.uri = request.uri.replace(user_name, REDACTED_STRING)

    return request


def redact_key_values(keys_to_redact):
    def redact(payload):
        for key in keys_to_redact:
            if key in payload:
                payload[key] = REDACTED_STRING
        return payload

    def before_record_response(response):
        body = response["body"]["string"].decode("utf8")

        with contextlib.suppress(json.JSONDecodeError):
            payload = json.loads(body)
            redacted_payload = (
                list(map(redact, payload))
                if isinstance(payload, list)
                else redact(payload)
            )
            response["body"]["string"] = json.dumps(redacted_payload).encode()

        return response

    return before_record_response


class TestResults(VCRTestCase):
    def _get_vcr(self, **kwargs):
        myvcr = super()._get_vcr(**kwargs)
        myvcr.cassette_library_dir = "tests/unit/fixtures/vcr_cassettes"
        myvcr.decode_compressed_response = True
        # Header matching is not set by default, we need that to test the
        # search-after functionality is performing correctly.
        myvcr.match_on = [
            "method",
            "scheme",
            "host",
            "port",
            "path",
            "query",
            "headers",
        ]
        myvcr.filter_headers = [
            "Accept-Encoding",
            "Authorization",
            "Cookie",
            "Set-Cookie",
            "User-Agent",
        ]
        myvcr.filter_query_parameters = [
            ("client_id", REDACTED_STRING),
        ]

        myvcr.before_record_response = redact_key_values(
            [
                "access_token",
                "uid",
                "first_name",
                "last_name",
                "email_address",
                "nams_auid",
            ]
        )

        myvcr.before_record_request = redact_login_request

        return myvcr

    def test_no_results(self):
        """If we search for a collection that doesn't exist, we should get no results."""
        granules = earthaccess.search_data(
            # STAC collection name; correct short name is OPERA_L3_DSWX-HLS_V1
            # Example discussed in: https://github.com/nsidc/earthaccess/pull/839
            short_name="OPERA_L3_DSWX-HLS_V1_1.0",
            bounding_box=(-95.19, 30.59, -94.99, 30.79),
            temporal=("2024-04-30", "2024-05-31"),
        )
        assert len(granules) == 0

    def test_data_links(self):
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
        assert g.data_links(access="external", in_region=True)[0].startswith("https://")
        assert g.data_links(access="external", in_region=False)[0].startswith(
            "https://"
        )

    def test_get_more_than_2000(self):
        """If we execute a get with a limit of more than 2000
        then we expect multiple invocations of a cmr granule search and
        to not fetch back more results than we ask for.
        """
        granules = earthaccess.search_data(short_name="MOD02QKM", count=3000)

        # Assert that we performed one 'hits' search and two 'results' search queries
        self.assertEqual(len(self.cassette), 3)
        self.assertEqual(len(granules), 4000)
        self.assertTrue(unique_results(granules))

    def test_get(self):
        """If we execute a get with no arguments then we expect
        to get the maximum no. of granules from a single CMR call (2000)
        in a single request.
        """
        granules = earthaccess.search_data(short_name="MOD02QKM", count=2000)

        # Assert that we performed one 'hits' search and one 'results' search queries
        self.assertEqual(len(self.cassette), 2)
        self.assertEqual(len(granules), 2000)
        self.assertTrue(unique_results(granules))

    def test_get_all_less_than_2k(self):
        """If we execute a get_all then we expect multiple
        invocations of a cmr granule search and
        to not fetch back more results than we ask for.
        """
        granules = earthaccess.search_data(
            short_name="TELLUS_GRAC_L3_JPL_RL06_LND_v04", count=2000
        )

        # Assert that we performed a hits query and one search results query
        self.assertEqual(len(self.cassette), 2)
        self.assertEqual(len(granules), 163)
        self.assertTrue(unique_results(granules))

    def test_get_all_more_than_2k(self):
        """If we execute a get_all then we expect multiple
        invocations of a cmr granule search and
        to not fetch back more results than we ask for.
        """
        granules = earthaccess.search_data(
            short_name="CYGNSS_NOAA_L2_SWSP_25KM_V1.2", count=3000
        )

        # Assert that we performed a hits query and two search results queries
        self.assertEqual(len(self.cassette), 3)
        self.assertEqual(
            len(granules), int(self.cassette.responses[0]["headers"]["CMR-Hits"][0])
        )
        self.assertEqual(
            len(granules),
            min(3000, int(self.cassette.responses[0]["headers"]["CMR-Hits"][0])),
        )
        self.assertTrue(unique_results(granules))

    def test_collections_less_than_2k(self):
        """If we execute a get_all then we expect multiple
        invocations of a cmr granule search and
        to not fetch back more results than we ask for.
        """
        query = DataCollections().daac("PODAAC").cloud_hosted(True)
        collections = query.get(20)

        # Assert that we performed a single search results query
        self.assertEqual(len(self.cassette), 1)
        self.assertEqual(len(collections), 20)
        self.assertTrue(unique_results(collections))
        self.assert_is_using_search_after(self.cassette)

    def test_collections_more_than_2k(self):
        """If we execute a get_all then we expect multiple
        invocations of a cmr granule search and
        to not fetch back more results than we ask for.
        """
        query = DataCollections()
        collections = query.get(3000)

        # Assert that we performed two search results queries
        self.assertEqual(len(self.cassette), 2)
        self.assertEqual(len(collections), 4000)
        self.assertTrue(unique_results(collections))
        self.assert_is_using_search_after(self.cassette)

    def assert_is_using_search_after(self, cass):
        first_request = True

        for request in cass.requests:
            # Verify the page number was not used
            self.assertTrue("page_num" not in request.uri)
            # Verify that Search After was used in all requests except first
            self.assertEqual(first_request, "CMR-Search-After" not in request.headers)
            first_request = False


def test_get_doi_returns_doi_when_present():
    collection = DataCollection(
        {"umm": {"DOI": {"DOI": "doi:10.16904/envidat.lwf.34"}}, "meta": {}}
    )

    assert collection.doi() == "doi:10.16904/envidat.lwf.34"


def test_get_doi_returns_empty_string_when_doi_missing():
    collection = DataCollection({"umm": {"DOI": {}}, "meta": {}})

    assert collection.doi() is None


def test_get_doi_returns_empty_string_when_doi_key_missing():
    collection = DataCollection({"umm": {}, "meta": {}})

    assert collection.doi() is None


@responses.activate
def test_get_citation_apa_format():
    collection = DataCollection(
        {"umm": {"DOI": {"DOI": "doi:10.16904/envidat.lwf.34"}}, "meta": {}}
    )

    responses.add(
        responses.GET,
        "https://citation.doi.org/format?doi=doi:10.16904/envidat.lwf.34&style=apa&lang=en-US",
        body="Meusburger, K., Graf Pannatier, E., & Schaub, M. (2019). 10-HS Pfynwald (Version 2019) [Dataset]. EnviDat. https://doi.org/10.16904/ENVIDAT.LWF.34",
        status=200,
    )

    citation = collection.citation(format="apa", language="en-US")

    assert (
        citation
        == "Meusburger, K., Graf Pannatier, E., & Schaub, M. (2019). 10-HS Pfynwald (Version 2019) [Dataset]. EnviDat. https://doi.org/10.16904/ENVIDAT.LWF.34"
    )


@responses.activate
def test_get_citation_different_language():
    collection = DataCollection(
        {"umm": {"DOI": {"DOI": "doi:10.16904/envidat.lwf.34"}}, "meta": {}}
    )

    responses.add(
        responses.GET,
        "https://citation.doi.org/format?doi=doi:10.16904/envidat.lwf.34&style=apa&lang=fr-FR",
        body="Meusburger, K., Graf Pannatier, E., & Schaub, M. (2019). 10-HS Pfynwald (Version 2019) [Jeu de données]. EnviDat. https://doi.org/10.16904/ENVIDAT.LWF.34",
        status=200,
    )

    citation = collection.citation(format="apa", language="fr-FR")

    assert (
        citation
        == "Meusburger, K., Graf Pannatier, E., & Schaub, M. (2019). 10-HS Pfynwald (Version 2019) [Jeu de données]. EnviDat. https://doi.org/10.16904/ENVIDAT.LWF.34"
    )


def test_get_citation_returns_none_when_doi_missing():
    collection = DataCollection({"umm": {}, "meta": {}})

    assert collection.citation(format="apa", language="en-US") is None


def test_get_citation_returns_none_when_doi_empty():
    collection = DataCollection({"umm": {"DOI": {"DOI": ""}}, "meta": {}})

    assert collection.citation(format="apa", language="en-US") is None
