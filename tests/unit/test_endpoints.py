"""
Unit tests for endpoints.py

Pure unit tests for the CMR endpoint crawler utility functions.
Tests pure functions with no I/O or external dependencies.

For integration tests with mocked/real API calls, see:
    tests/integration/test_endpoints.py
"""

import pytest
from earthaccess.endpoints import (
    create_bucket_key_mapping_recursive,
    extract_bucket_prefix_key,
)


# =============================================================================
# Test Constants - Standardized URLs and S3 Paths
# =============================================================================

# Standard S3 Credentials API Endpoints
ENDPOINT_1 = "https://data.test1.nasa.gov/s3credentials"
ENDPOINT_2 = "https://data.test2.nasa.gov/s3credentials"
ENDPOINT_3 = "https://data.test3.nasa.gov/s3credentials"

# Standard S3 Bucket Paths
BUCKET_A = "s3://test-bucket-a/data"
BUCKET_A_FILE = "s3://test-bucket-a/data/file.nc"
BUCKET_B = "s3://test-bucket-b/data"
BUCKET_C = "s3://test-bucket-c/archive"

# Shared bucket with different prefixes
SHARED_BUCKET_PREFIX_A = "s3://test-shared-bucket/prefix-a/file.nc"
SHARED_BUCKET_PREFIX_B = "s3://test-shared-bucket/prefix-b/file.nc"

# Nested paths for conflict resolution testing
NESTED_2023 = "s3://test-bucket-a/data/2023/jan/file.nc"
NESTED_2024 = "s3://test-bucket-a/data/2024/jan/file.nc"

# Deep paths for max_depth testing
DEEP_PATH_1 = "s3://test-bucket-a/path/subpath/file1.nc"
DEEP_PATH_2 = "s3://test-bucket-a/path/subpath/file2.nc"

# Unique buckets for mixed conflict testing
UNIQUE_BUCKET_A = "s3://test-unique-bucket-a/data"
UNIQUE_BUCKET_B = "s3://test-unique-bucket-b/data"


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
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": [BUCKET_A_FILE]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        assert len(mapping) == 1
        assert "test-bucket-a" in mapping
        assert mapping["test-bucket-a"] == ENDPOINT_1

    def test_different_buckets_no_conflicts(self):
        """Test that different buckets map to different endpoints without conflicts."""
        results = {
            "C1234": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": [BUCKET_A]
            },
            "C5678": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [BUCKET_B]
            },
            "C9012": {
                "S3CredentialsAPIEndpoint": ENDPOINT_3,
                "S3BucketAndObjectPrefixNames": [BUCKET_C]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        assert len(mapping) == 3
        assert mapping["test-bucket-a"] == ENDPOINT_1
        assert mapping["test-bucket-b"] == ENDPOINT_2
        assert mapping["test-bucket-c"] == ENDPOINT_3

    def test_same_bucket_different_prefixes_resolves_at_depth_1(self):
        """Test that conflicts at bucket level are resolved at prefix level."""
        results = {
            "C1234": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": [SHARED_BUCKET_PREFIX_A]
            },
            "C5678": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [SHARED_BUCKET_PREFIX_B]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # Should resolve to depth 1 since prefixes differ
        assert len(mapping) == 2
        assert "test-shared-bucket/prefix-a" in mapping
        assert "test-shared-bucket/prefix-b" in mapping
        assert mapping["test-shared-bucket/prefix-a"] == ENDPOINT_1
        assert mapping["test-shared-bucket/prefix-b"] == ENDPOINT_2

    def test_conflict_resolution_at_depth_2(self):
        """Test that conflicts are resolved at appropriate depth."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": [NESTED_2023]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [NESTED_2024]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # Should resolve at depth 2
        assert "test-bucket-a/data/2023" in mapping
        assert "test-bucket-a/data/2024" in mapping

    def test_unresolvable_conflict_at_max_depth(self):
        """Test that ValueError is raised when max_depth is insufficient to resolve conflicts."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": [DEEP_PATH_1]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [DEEP_PATH_2]
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
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": [BUCKET_A_FILE]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [BUCKET_A_FILE]
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
                "S3BucketAndObjectPrefixNames": [BUCKET_A]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [BUCKET_B]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # Should only map bucket-b (C1 is skipped)
        assert len(mapping) == 1
        assert "test-bucket-b" in mapping

    def test_missing_s3bucket_names(self):
        """Test that entries without S3BucketAndObjectPrefixNames are skipped."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1
                # Missing S3BucketAndObjectPrefixNames
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [BUCKET_B]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        assert len(mapping) == 1
        assert "test-bucket-b" in mapping

    def test_empty_s3bucket_names_list(self):
        """Test that entries with empty S3BucketAndObjectPrefixNames list are skipped."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": []  # Empty list
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [BUCKET_B]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        assert len(mapping) == 1
        assert "test-bucket-b" in mapping

    def test_multiple_paths_same_collection_same_endpoint(self):
        """Test collection with multiple S3 paths to same endpoint."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": [
                    "s3://test-bucket-a/path1/data",
                    "s3://test-bucket-a/path2/data",
                    BUCKET_B + "/archive"
                ]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # All paths should map to the same endpoint
        assert all(endpoint == ENDPOINT_1 for endpoint in mapping.values())

    def test_multiple_paths_some_conflicting(self):
        """Test mix of conflicting and non-conflicting paths."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": [
                    UNIQUE_BUCKET_A,
                    "s3://test-shared-bucket/prefix-a/data"
                ]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": [
                    UNIQUE_BUCKET_B,
                    "s3://test-shared-bucket/prefix-b/data"
                ]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=5)

        # Unique buckets should resolve at depth 0
        assert any("test-unique-bucket-a" in key for key in mapping.keys())
        assert any("test-unique-bucket-b" in key for key in mapping.keys())
        # Shared bucket should resolve at depth 1
        assert "test-shared-bucket/prefix-a" in mapping or any("prefix-a" in key for key in mapping.keys())

    def test_max_depth_0_only_buckets(self):
        """Test that max_depth=0 only uses bucket-level keys."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": ["s3://test-bucket-a/any/path/here"]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": ["s3://test-bucket-b/different/path"]
            }
        }
        mapping = create_bucket_key_mapping_recursive(results, max_depth=0)

        # Should only have bucket-level keys
        assert "test-bucket-a" in mapping
        assert "test-bucket-b" in mapping
        assert all('/' not in key for key in mapping.keys())

    def test_error_max_depth(self):
        """Test that ValueError is raised when conflict persists at max_depth."""
        results = {
            "C1": {
                "S3CredentialsAPIEndpoint": ENDPOINT_2,
                "S3BucketAndObjectPrefixNames": ["s3://test-bucket-a/with/deep/path/file.nc"]
            },
            "C2": {
                "S3CredentialsAPIEndpoint": ENDPOINT_1,
                "S3BucketAndObjectPrefixNames": ["s3://test-bucket-a/with/deep/path/file.nc"]
            }
        }
        # At max_depth=2, paths are identical so conflict cannot be resolved
        # Should raise ValueError instead of picking alphabetically
        with pytest.raises(ValueError, match="Cannot resolve conflicts at max_depth=2"):
            create_bucket_key_mapping_recursive(results, max_depth=2)
