"""
Test module for endpoints.py

Comprehensive unit tests and integration tests for the CMR endpoint crawler.

Install test dependencies:
    pip install pytest pytest-asyncio aioresponses

Run tests:
    pytest test_endpoints.py -v
"""

import pytest
import re
from aioresponses import aioresponses

from endpoints import (
    extract_bucket_prefix_key,
    create_bucket_key_mapping_recursive,
    query_cmr_async,
    crawl_cmr_endpoints,
)

# Pattern to match CMR URLs with any query parameters
CMR_URL_PATTERN = re.compile(r'https://cmr\.earthdata\.nasa\.gov/search/collections\.umm_json.*')


# =============================================================================
# Unit Tests: extract_bucket_prefix_key
# =============================================================================

class TestExtractBucketPrefixKey:
    """Test the bucket/prefix key extraction function."""
    @pytest.mark.parametrize("url, depth, expected", [
        ("s3://my-bucket/prefix1/prefix2/prefix3/file.txt", 0 , "my-bucket"),
        ("s3://my-bucket/prefix1/prefix2/prefix3/file.txt", 1, "my-bucket/prefix1"),
        ("s3://my-bucket/prefix1/prefix2/prefix3/file.txt", 2, "my-bucket/prefix1/prefix2"),
        ("s3://my-bucket/prefix1/prefix2/prefix3/file.txt", 3, "my-bucket/prefix1/prefix2/prefix3"),
    ])
    def test_different_depths(self, url, depth, expected):
        """Test extraction at various depths."""
        assert extract_bucket_prefix_key(url, depth) == expected

    def test_depth_exceeds_available_components(self):
        """Test that depth greater than path length returns entire path."""
        path = "s3://my-bucket/data"
        assert extract_bucket_prefix_key(path, 10) == "my-bucket/data"
        assert extract_bucket_prefix_key(path, 100) == "my-bucket/data"

    def test_path_without_s3_prefix(self):
        """Test extraction works even without s3:// prefix."""
        assert extract_bucket_prefix_key("my-bucket/data/file.txt", 0) == "my-bucket"
        assert extract_bucket_prefix_key("my-bucket/data/file.txt", 1) == "my-bucket/data"

    def test_bucket_only_path(self):
        """Test extraction with bucket-only path (no prefixes)."""
        assert extract_bucket_prefix_key("s3://my-bucket", 0) == "my-bucket"
        assert extract_bucket_prefix_key("s3://my-bucket", 1) == "my-bucket"
        assert extract_bucket_prefix_key("my-bucket", 0) == "my-bucket"

    def test_trailing_slash(self):
        """Test handling of paths with trailing slashes."""
        assert extract_bucket_prefix_key("s3://bucket/prefix/", 0) == "bucket"
        assert extract_bucket_prefix_key("s3://bucket/prefix/", 1) == "bucket/prefix"

    def test_empty_prefix_components(self):
        """Test handling of paths with multiple consecutive slashes."""
        # These shouldn't normally occur but let's ensure we handle them
        path = "s3://bucket//data//file.txt"
        result = extract_bucket_prefix_key(path, 1)
        # Should still extract bucket + first non-empty component
        assert "bucket" in result

# =============================================================================
# Unit Tests: create_bucket_key_mapping_recursive
# =============================================================================

class TestCreateBucketKeyMappingRecursive:
    """Test the recursive bucket mapping function with conflict resolution."""

    def test_empty_input(self):
        """Test that empty input returns empty mapping."""
        mapping = create_bucket_key_mapping_recursive({}, max_depth=5)
        assert mapping == {}

    def test_single_entry_no_conflicts(self):
        """Test single entry creates simple mapping."""
        results = {
            "C1234": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-a/data/file.nc"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        assert len(mapping) == 1
        assert "bucket-a" in mapping
        assert mapping["bucket-a"] == "https://endpoint1.nasa.gov"

    def test_different_buckets_no_conflicts(self):
        """Test that different buckets map to different endpoints without conflicts."""
        results = {
            "C1234": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-a/data"]
            },
            "C5678": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-b/data"]
            },
            "C9012": {
                "S3CredentialsAPIEndpoint": "https://endpoint3.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-c/archive"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        assert len(mapping) == 3
        assert mapping["bucket-a"] == "https://endpoint1.nasa.gov"
        assert mapping["bucket-b"] == "https://endpoint2.nasa.gov"
        assert mapping["bucket-c"] == "https://endpoint3.nasa.gov"

    def test_same_bucket_different_prefixes_resolves_at_depth_1(self):
        """Test that conflicts at bucket level are resolved at prefix level."""
        results = {
            "C1234": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://shared-bucket/data-a/file.nc"]
            },
            "C5678": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://shared-bucket/data-b/file.nc"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # Should resolve to depth 1 since prefixes differ
        assert len(mapping) == 2
        assert "shared-bucket/data-a" in mapping
        assert "shared-bucket/data-b" in mapping
        assert mapping["shared-bucket/data-a"] == "https://endpoint1.nasa.gov"
        assert mapping["shared-bucket/data-b"] == "https://endpoint2.nasa.gov"

    def test_conflict_resolution_at_depth_2(self):
        """Test that conflicts are resolved at appropriate depth."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket/data/2023/jan/file.nc"]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket/data/2024/jan/file.nc"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # Should resolve at depth 2
        assert "bucket/data/2023" in mapping
        assert "bucket/data/2024" in mapping

    def test_unresolvable_conflict_at_max_depth(self):
        """Test that ValueError is raised when max_depth is insufficient to resolve conflicts."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket/path/subpath/file1.nc"]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket/path/subpath/file2.nc"]
            }
        }
        # Use max_depth=2, which is insufficient to resolve conflict
        with pytest.raises(ValueError, match="Cannot resolve conflicts at max_depth=2"):
            create_bucket_key_mapping_recursive(results, max_depth=2)

    #TODO: See https://github.com/nsidc/earthaccess/pull/1135#issuecomment-3568296390
    # Maybe we should support conflict resolution with preference of a certain domain?
    # Seems like overkill for now
    def test_unresolvable_conflict_identical_paths(self):
        """Test that ValueError is raised when paths are completely identical."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket/data/file.nc"]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket/data/file.nc"]
            }
        }
        # Should raise ValueError since paths are identical even at max_depth
        with pytest.raises(ValueError, match="Cannot resolve conflicts at max_depth=10"):
            create_bucket_key_mapping_recursive(results, max_depth=10)

    #TODO: ensure this is actually logged in debug mode.
    def test_missing_s3credentials_endpoint(self):
        """Test that entries without S3CredentialsAPIEndpoint are skipped."""
        results = {
            "C1": {
                # Missing S3CredentialsAPIEndpoint
                "S3BucketAndObjectPrefixNames": ["s3://bucket-a/data"]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-b/data"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # Should only map bucket-b (C1 is skipped)
        assert len(mapping) == 1
        assert "bucket-b" in mapping

    def test_missing_s3bucket_names(self):
        """Test that entries without S3BucketAndObjectPrefixNames are skipped."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov"
                # Missing S3BucketAndObjectPrefixNames
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-b/data"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        assert len(mapping) == 1
        assert "bucket-b" in mapping

    def test_empty_s3bucket_names_list(self):
        """Test that entries with empty S3BucketAndObjectPrefixNames list are skipped."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": []  # Empty list
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-b/data"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        assert len(mapping) == 1
        assert "bucket-b" in mapping

    def test_multiple_paths_same_collection_same_endpoint(self):
        """Test collection with multiple S3 paths to same endpoint."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": [
                    "s3://bucket-a/path1/data",
                    "s3://bucket-a/path2/data",
                    "s3://bucket-b/archive"
                ]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # All paths should map to the same endpoint
        assert all(endpoint == "https://endpoint1.nasa.gov" for endpoint in mapping.values())

    def test_multiple_paths_some_conflicting(self):
        """Test mix of conflicting and non-conflicting paths."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": [
                    "s3://unique-bucket-a/data",
                    "s3://shared-bucket/type-a/data"
                ]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": [
                    "s3://unique-bucket-b/data",
                    "s3://shared-bucket/type-b/data"
                ]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # Unique buckets should resolve at depth 0
        assert any("unique-bucket-a" in key for key in mapping.keys())
        assert any("unique-bucket-b" in key for key in mapping.keys())
        # Shared bucket should resolve at depth 1
        assert "shared-bucket/type-a" in mapping or any("type-a" in key for key in mapping.keys())

    def test_max_depth_0_only_buckets(self):
        """Test that max_depth=0 only uses bucket-level keys."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-a/any/path/here"]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket-b/different/path"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=0)

        # Should only have bucket-level keys
        assert "bucket-a" in mapping
        assert "bucket-b" in mapping
        assert all('/' not in key for key in mapping.keys())

    def test_conflict_picked_alphabetically_at_max_depth(self):
        """Test that ValueError is raised when conflict persists at max_depth."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": "https://zebra.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket/path/file.nc"]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": "https://alpha.nasa.gov",
                "S3BucketAndObjectPrefixNames": ["s3://bucket/path/file.nc"]
            }
        }
        # At max_depth=2, paths are identical so conflict cannot be resolved
        # Should raise ValueError instead of picking alphabetically
        with pytest.raises(ValueError, match="Cannot resolve conflicts at max_depth=2"):
            create_bucket_key_mapping_recursive(results, max_depth=2)


# =============================================================================
# Integration Tests with Mocking: query_cmr_async
# =============================================================================

class TestQueryCMRAsyncWithMocking:
    """Test CMR API query function with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_single_page_response(self):
        """Test querying when all results fit in one page."""
        mock_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1234"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket-a/data"]
                        }
                    }
                },
                {
                    "meta": {"concept-id": "C5678"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket-b/archive"]
                        }
                    }
                }
            ]
        }

        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True
            )

            results = await query_cmr_async(page_size=100, max_results=100)

            assert len(results) == 2
            assert "C1234" in results
            assert "C5678" in results
            assert results["C1234"]["S3CredentialsAPIEndpoint"] == "https://endpoint1.nasa.gov"
            assert results["C5678"]["S3CredentialsAPIEndpoint"] == "https://endpoint2.nasa.gov"

    @pytest.mark.asyncio
    async def test_multiple_pages(self):
        """Test querying when results span multiple pages."""
        # Page 1
        page1_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket-1/data"]
                        }
                    }
                }
            ]
        }

        # Page 2
        page2_response = {
            "items": [
                {
                    "meta": {"concept-id": "C2"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket-2/data"]
                        }
                    }
                }
            ]
        }

        with aioresponses() as mock:
            # Mock both pages with pattern matching
            mock.get(
                CMR_URL_PATTERN,
                payload=page1_response,
                headers={"CMR-Hits": "2"}
            )
            mock.get(
                CMR_URL_PATTERN,
                payload=page2_response,
                headers={"CMR-Hits": "2"}
            )

            results = await query_cmr_async(page_size=1, concurrent_requests=5)

            assert len(results) == 2
            assert "C1" in results
            assert "C2" in results

    @pytest.mark.asyncio
    async def test_max_results_limits_fetching(self):
        """Test that max_results parameter limits the number of results fetched."""
        page_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket/data"]
                        }
                    }
                }
            ]
        }

        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload=page_response,
                headers={"CMR-Hits": "1000"},
                repeat=True
            )

            results = await query_cmr_async(page_size=100, max_results=100)

            # Should only fetch 1 page (max_results=100, page_size=100)
            assert len(results) <= 100

    @pytest.mark.asyncio
    async def test_empty_response(self):
        """Test handling of empty API response."""
        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload={"items": []},
                headers={"CMR-Hits": "0"}
            )

            results = await query_cmr_async(page_size=100)

            assert results == {}

    @pytest.mark.asyncio
    async def test_items_without_direct_distribution(self):
        """Test that items without DirectDistributionInformation are skipped."""
        mock_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1"},
                    "umm": {}  # No DirectDistributionInformation
                },
                {
                    "meta": {"concept-id": "C2"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket/data"]
                        }
                    }
                }
            ]
        }

        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True
            )

            results = await query_cmr_async(page_size=100)

            # Only C2 should be in results
            assert len(results) == 1
            assert "C2" in results
            assert "C1" not in results

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test that API errors are handled gracefully."""
        with aioresponses() as mock:
            mock.get(CMR_URL_PATTERN, status=500)

            results = await query_cmr_async(page_size=100)

            # Should return empty dict on error
            assert results == {}


# =============================================================================
# Integration Tests with Mocking: crawl_cmr_endpoints
# =============================================================================

class TestCrawlCMREndpointsWithMocking:
    """Test the main crawl function with mocked API responses."""

    @pytest.mark.asyncio
    async def test_successful_crawl_no_conflicts(self):
        """Test successful crawl with no conflicts."""
        mock_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket-a/data"]
                        }
                    }
                },
                {
                    "meta": {"concept-id": "C2"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket-b/data"]
                        }
                    }
                }
            ]
        }

        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True
            )

            mapping = await crawl_cmr_endpoints(max_depth=5, max_results=100)

            assert len(mapping) == 2
            assert "bucket-a" in mapping
            assert "bucket-b" in mapping
            assert mapping["bucket-a"] == "https://endpoint1.nasa.gov"
            assert mapping["bucket-b"] == "https://endpoint2.nasa.gov"

    @pytest.mark.asyncio
    async def test_crawl_resolves_conflicts_at_depth_1(self):
        """Test that conflicts are resolved by increasing depth."""
        mock_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://shared/data-a/file.nc"]
                        }
                    }
                },
                {
                    "meta": {"concept-id": "C2"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://shared/data-b/file.nc"]
                        }
                    }
                }
            ]
        }

        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True
            )

            mapping = await crawl_cmr_endpoints(max_depth=5, max_results=100)

            # Should resolve at depth 1
            assert len(mapping) == 2
            assert "shared/data-a" in mapping
            assert "shared/data-b" in mapping

    @pytest.mark.asyncio
    async def test_crawl_raises_on_unresolvable_conflicts(self):
        """Test that ValueError is raised when conflicts can't be resolved."""
        mock_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint1.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket/path/deep/file1.nc"]
                        }
                    }
                },
                {
                    "meta": {"concept-id": "C2"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint2.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket/path/deep/file2.nc"]
                        }
                    }
                }
            ]
        }

        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True
            )

            # Use low max_depth to ensure conflicts aren't resolved
            with pytest.raises(ValueError, match="Cannot resolve conflicts at max_depth=2"):
                await crawl_cmr_endpoints(max_depth=2, max_results=100)

    @pytest.mark.asyncio
    async def test_crawl_raises_on_no_results(self):
        """Test that RuntimeError is raised when no results are found."""
        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload={"items": []},
                headers={"CMR-Hits": "0"}
            )

            with pytest.raises(RuntimeError, match="No results collected from CMR API"):
                await crawl_cmr_endpoints(max_depth=5)

    @pytest.mark.asyncio
    async def test_crawl_with_multiple_collections_per_endpoint(self):
        """Test crawling with multiple collections pointing to same endpoint."""
        mock_response = {
            "items": [
                {
                    "meta": {"concept-id": "C1"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint.nasa.gov",
                            "S3BucketAndObjectPrefixNames": ["s3://bucket-a/data"]
                        }
                    }
                },
                {
                    "meta": {"concept-id": "C2"},
                    "umm": {
                        "DirectDistributionInformation": {
                            "S3CredentialsAPIEndpoint": "https://endpoint.nasa.gov",  # Same endpoint
                            "S3BucketAndObjectPrefixNames": ["s3://bucket-b/data"]
                        }
                    }
                }
            ]
        }

        with aioresponses() as mock:
            mock.get(
                CMR_URL_PATTERN,
                payload=mock_response,
                headers={"CMR-Hits": "2"},
                repeat=True
            )

            mapping = await crawl_cmr_endpoints(max_depth=5, max_results=100)

            assert len(mapping) == 2
            assert mapping["bucket-a"] == "https://endpoint.nasa.gov"
            assert mapping["bucket-b"] == "https://endpoint.nasa.gov"


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
