"""Tests for search_data.  This needs a mock to be set up but for now, I get all
the first 10 granules using count=10
"""

import earthaccess

# Number of granules to return passed to count, also expected number returned
expected_count = 10

# I use ATL10 as a test case
short_name = "ATL10"
version = "006"  # This may need to be upped
provider = "NSIDC_CPRD"
daac = "NSIDC"
data_center = "NSIDC"


def test_search_data_by_shortname():
    """Tests granule search by short name returns
    results that match expected_count"""
    results = earthaccess.search_data(
        short_name=short_name,
        count=expected_count)
    assert len(results) == expected_count


def test_search_data_with_version():
    """Tests granule search by short name and version
    returned expected_count"""
    results = earthaccess.search_data(
        short_name=short_name,
        version=version,
        count=expected_count)
    assert len(results) == expected_count


def test_search_data_by_provider():
    """Tests granule search by provider returns
    expected_count
    """
    results = earthaccess.search_data(
        provider=provider,
        count=expected_count,
        )
    assert len(results) == expected_count


def test_search_data_by_daac():
    """Tests granule search by daac returns
    expected_count
    """
    results = earthaccess.search_data(
        daac=daac,
        count=expected_count,
        )
    assert len(results) == expected_count


def test_search_data_by_data_center():
    """Tests granule search by data_center returns
    expected_count
    """
    results = earthaccess.search_data(
        data_center=data_center,
        count=expected_count,
        )
    assert len(results) == expected_count

