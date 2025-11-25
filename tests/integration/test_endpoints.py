"""
Integration tests for endpoints.py

Tests for the CMR endpoint crawler with mocked and real API interactions.

Install test dependencies:
    pip install pytest pytest-asyncio aioresponses

Run tests:
    pytest tests/integration/test_endpoints.py -v

Run with real API tests (use sparingly):
    pytest tests/integration/test_endpoints.py -v -m realapi
"""

import re

import pytest
from aioresponses import aioresponses

from earthaccess.endpoints import (
    query_cmr_async,
    crawl_cmr_endpoints,
)


# =============================================================================
# Test Fixtures and Constants
# =============================================================================


@pytest.fixture
def cmr_url_pattern():
    """Regex pattern for matching CMR API URLs with any query parameters."""
    return re.compile(
        r"https://cmr\.earthdata\.nasa\.gov/search/collections\.umm_json.*"
    )


@pytest.fixture
def standard_endpoints():
    """Standard test endpoint URLs for consistency across tests."""
    return {
        1: "https://data.test1.nasa.gov/s3credentials",
        2: "https://data.test2.nasa.gov/s3credentials",
        3: "https://data.test3.nasa.gov/s3credentials",
    }


@pytest.fixture
def standard_buckets():
    """Standard S3 bucket/prefix patterns for consistency across tests."""
    return {
        "bucket_a": "s3://test-bucket-a/data",
        "bucket_b": "s3://test-bucket-b/data",
        "bucket_c": "s3://test-bucket-c/archive",
        "shared_prefix_a": "s3://test-shared-bucket/prefix-a/data",
        "shared_prefix_b": "s3://test-shared-bucket/prefix-b/data",
        "nested_2023": "s3://test-bucket-a/data/2023/file.nc",
        "nested_2024": "s3://test-bucket-a/data/2024/file.nc",
        "deep_path_1": "s3://test-bucket-a/path/deep/file1.nc",
        "deep_path_2": "s3://test-bucket-a/path/deep/file2.nc",
    }


@pytest.fixture
def mock_cmr_collection():
    """Factory fixture for creating mock CMR collection responses.

    Usage:
        mock_response = mock_cmr_collection([
            ("C1234", endpoints[1], [buckets["bucket_a"]]),
            ("C5678", endpoints[2], [buckets["bucket_b"]]),
        ])
    """

    def _create_response(collections):
        """Create a mock CMR response with the given collections.

        Parameters:
            collections: List of tuples (concept_id, endpoint_url, s3_paths_list)

        Returns:
            Dict representing a CMR API response
        """
        return {
            "items": [
                {
                    "meta": {"concept-id": cid},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": endpoint,
                            "S3BucketAndObjectPrefixNames": paths,
                        }
                    },
                }
                for cid, endpoint, paths in collections
            ]
        }

    return _create_response


# =============================================================================
# Integration Tests with Mocking: query_cmr_async
# =============================================================================


class TestQueryCMRAsyncWithMocking:
    """Test CMR API query function with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_single_page_response(
        self, cmr_url_pattern, mock_cmr_collection, standard_endpoints, standard_buckets
    ):
        """Test querying when all results fit in one page."""
        mock_response = mock_cmr_collection(
            [
                ("C1234", standard_endpoints[1], [standard_buckets["bucket_a"]]),
                ("C5678", standard_endpoints[2], [standard_buckets["bucket_b"]]),
            ]
        )

        with aioresponses() as mock:
            mock.get(
                cmr_url_pattern,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True,
            )

            results = await query_cmr_async(page_size=100, max_results=100)

            assert len(results) == 2
            assert "C1234" in results
            assert "C5678" in results
            assert results["C1234"]["S3CredentialsAPIEndpoint"] == standard_endpoints[1]
            assert results["C5678"]["S3CredentialsAPIEndpoint"] == standard_endpoints[2]

    @pytest.mark.asyncio
    async def test_multiple_pages(
        self, cmr_url_pattern, mock_cmr_collection, standard_endpoints, standard_buckets
    ):
        """Test querying when results span multiple pages."""
        # Page 1
        page1_response = mock_cmr_collection(
            [("C1", standard_endpoints[1], [standard_buckets["bucket_a"]])]
        )

        # Page 2
        page2_response = mock_cmr_collection(
            [("C2", standard_endpoints[2], [standard_buckets["bucket_b"]])]
        )

        with aioresponses() as mock:
            # Mock both pages with pattern matching
            mock.get(
                cmr_url_pattern, payload=page1_response, headers={"CMR-Hits": "2"}
            )
            mock.get(
                cmr_url_pattern, payload=page2_response, headers={"CMR-Hits": "2"}
            )

            results = await query_cmr_async(page_size=1, concurrent_requests=5)

            assert len(results) == 2
            assert "C1" in results
            assert "C2" in results

    @pytest.mark.asyncio
    async def test_max_results_limits_fetching(
        self, cmr_url_pattern, mock_cmr_collection, standard_endpoints, standard_buckets
    ):
        """Test that max_results parameter limits the number of results fetched."""
        # Page 1
        page1_response = mock_cmr_collection(
            [("C1", standard_endpoints[1], [standard_buckets["bucket_a"]])]
        )

        # Page 2
        page2_response = mock_cmr_collection(
            [("C2", standard_endpoints[2], [standard_buckets["bucket_b"]])]
        )

        with aioresponses() as mock:
            # Mock both pages with pattern matching
            mock.get(
                cmr_url_pattern, payload=page1_response, headers={"CMR-Hits": "2"}
            )
            mock.get(
                cmr_url_pattern, payload=page2_response, headers={"CMR-Hits": "2"}
            )

            results = await query_cmr_async(page_size=1, max_results=1)

            assert len(results) == 1
            assert "C1" in results
            assert "C2" not in results

    @pytest.mark.asyncio
    async def test_empty_response(self, cmr_url_pattern):
        """Test handling of empty API response."""
        with aioresponses() as mock:
            mock.get(
                cmr_url_pattern, payload={"items": []}, headers={"CMR-Hits": "0"}
            )

            results = await query_cmr_async()

            assert results == {}

    @pytest.mark.asyncio
    async def test_items_without_direct_distribution(
        self, cmr_url_pattern, mock_cmr_collection, standard_endpoints, standard_buckets
    ):
        """Test that items without DirectDistributionInformation are skipped."""
        mock_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1"},
                    "umm": {},  # No DirectDistributionInformation
                },
                {
                    "meta": {"concept-id": "C2"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": standard_endpoints[1],
                            "S3BucketAndObjectPrefixNames": [
                                standard_buckets["bucket_a"]
                            ],
                        }
                    },
                },
            ]
        }

        with aioresponses() as mock:
            mock.get(
                cmr_url_pattern,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True,
            )

            results = await query_cmr_async(page_size=100)

            # Only C2 should be in results
            assert len(results) == 1
            assert "C2" in results
            assert "C1" not in results

    @pytest.mark.asyncio
    async def test_api_error_handling(self, cmr_url_pattern):
        """Test that API errors are handled gracefully."""
        with aioresponses() as mock:
            mock.get(cmr_url_pattern, status=500)

            results = await query_cmr_async(page_size=100)

            # Should return empty dict on error
            assert results == {}


# =============================================================================
# Integration Tests with Mocking: crawl_cmr_endpoints
# =============================================================================


class TestCrawlCMREndpointsWithMocking:
    """Test the main crawl function with mocked API responses."""

    @pytest.mark.asyncio
    async def test_successful_crawl_no_conflicts(
        self, cmr_url_pattern, mock_cmr_collection, standard_endpoints, standard_buckets
    ):
        """Test successful crawl with no conflicts."""
        mock_response = mock_cmr_collection(
            [
                ("C1", standard_endpoints[1], [standard_buckets["bucket_a"]]),
                ("C2", standard_endpoints[2], [standard_buckets["bucket_b"]]),
            ]
        )

        with aioresponses() as mock:
            mock.get(
                cmr_url_pattern,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True,
            )

            mapping = await crawl_cmr_endpoints(max_depth=5, max_results=100)

            assert len(mapping) == 2
            assert "test-bucket-a" in mapping
            assert "test-bucket-b" in mapping
            assert mapping["test-bucket-a"] == standard_endpoints[1]
            assert mapping["test-bucket-b"] == standard_endpoints[2]

    @pytest.mark.asyncio
    async def test_crawl_resolves_conflicts_at_depth_1(
        self, cmr_url_pattern, mock_cmr_collection, standard_endpoints, standard_buckets
    ):
        """Test that conflicts are resolved by increasing depth."""
        mock_response = mock_cmr_collection(
            [
                ("C1", standard_endpoints[1], [standard_buckets["shared_prefix_a"]]),
                ("C2", standard_endpoints[2], [standard_buckets["shared_prefix_b"]]),
            ]
        )

        with aioresponses() as mock:
            mock.get(
                cmr_url_pattern,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True,
            )

            mapping = await crawl_cmr_endpoints(max_depth=5, max_results=100)

            # Should resolve at depth 1
            assert len(mapping) == 2
            assert "test-shared-bucket/prefix-a" in mapping
            assert "test-shared-bucket/prefix-b" in mapping

    @pytest.mark.asyncio
    async def test_crawl_raises_on_unresolvable_conflicts(
        self, cmr_url_pattern, mock_cmr_collection, standard_endpoints, standard_buckets
    ):
        """Test that ValueError is raised when conflicts can't be resolved."""
        mock_response = mock_cmr_collection(
            [
                ("C1", standard_endpoints[1], [standard_buckets["deep_path_1"]]),
                ("C2", standard_endpoints[2], [standard_buckets["deep_path_2"]]),
            ]
        )

        with aioresponses() as mock:
            mock.get(
                cmr_url_pattern,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True,
            )

            # Use low max_depth to ensure conflicts aren't resolved
            with pytest.raises(ValueError, match="Cannot resolve conflicts at max_depth=2"):
                await crawl_cmr_endpoints(max_depth=2, max_results=100)

    @pytest.mark.asyncio
    async def test_crawl_raises_on_no_results(self, cmr_url_pattern):
        """Test that RuntimeError is raised when no results are found."""
        with aioresponses() as mock:
            mock.get(
                cmr_url_pattern, payload={"items": []}, headers={"CMR-Hits": "0"}
            )

            with pytest.raises(RuntimeError, match="No results collected from CMR API"):
                await crawl_cmr_endpoints(max_depth=5)

    @pytest.mark.asyncio
    async def test_crawl_with_multiple_collections_per_endpoint(
        self, cmr_url_pattern, mock_cmr_collection, standard_endpoints, standard_buckets
    ):
        """Test crawling with multiple collections pointing to same endpoint."""
        mock_response = mock_cmr_collection(
            [
                ("C1", standard_endpoints[1], [standard_buckets["bucket_a"]]),
                ("C2", standard_endpoints[1], [standard_buckets["bucket_b"]]),  # Same endpoint
            ]
        )

        with aioresponses() as mock:
            mock.get(
                cmr_url_pattern,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True,
            )

            mapping = await crawl_cmr_endpoints(max_depth=5, max_results=100)

            assert len(mapping) == 2
            assert mapping["test-bucket-a"] == standard_endpoints[1]
            assert mapping["test-bucket-b"] == standard_endpoints[1]


# =============================================================================
# Integration Tests with Real API (Optional)
# =============================================================================


class TestIntegrationWithRealAPI:
    """
    Integration tests that hit the real CMR API.
    These are skipped by default. Run with: pytest -v -m realapi
    """

    @pytest.mark.realapi
    @pytest.mark.asyncio
    async def test_real_api_small_query(self):
        """Test with real API - fetch only 100 results."""
        # This actually hits the real API - use sparingly
        mapping = await crawl_cmr_endpoints(max_results=100, max_depth=5)

        assert isinstance(mapping, dict)
        assert len(mapping) > 0
        # All values should be URLs
        assert all(v.startswith("http") for v in mapping.values())
