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
orbit_number = 436
granule_name = "ATL10-02_20181014000347_02350101_006_02.h5"


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


def test_search_data_by_short_name_with_coud_hosted():
    """Tests granule search by short_name with only
    cloud_hosted granules
    """
    results = earthaccess.search_data(
        short_name=short_name,
        cloud_hosted=True,
        count=expected_count,
        )
    assert len(results) == expected_count


def test_search_data_by_short_name_with_online_only():
    """Tests granule search by short_name with online
    only granules 
    """
    results = earthaccess.search_data(
        short_name=short_name,
        online_only=True,
        count=expected_count,
        )
    assert len(results) == expected_count


def test_search_data_by_short_name_with_downloadable():
    """Tests granule search by short_name with downloadable
    granules 

    A granule is downloadable when it contains at least one RelatedURL of type GETDATA.
    """
    results = earthaccess.search_data(
        short_name=short_name,
        downloadable=True,
        count=expected_count,
        )
    assert len(results) == expected_count


def test_search_data_by_short_name_with_orbit_number():
    """Tests granule search by short_name with orbit_number
    """
    results = earthaccess.search_data(
        short_name=short_name,
        orbit_number=orbit_number,
        count=expected_count,
        )
    assert len(results) > 0


def test_search_data_by_short_name_with_granule_name():
    """Tests granule search by short_name and granule name"""
    results = earthaccess.search_data(
        short_name=short_name,
        granule_name=granule_name,
        )
    assert len(results) == 1


# day_night_flag returns 0 granules
#def test_search_data_by_short_name_with_day_night_flag():
#    """Tests granule search by short_name and granule name"""
#    results = earthaccess.search_data(
#        short_name="MOD10A1",
#        day_night_flag="Unspecified",
#        count=expected_count
#        )
#    assert len(results) > 0


def test_search_data_by_daac_with_instrument():
    """Test search_data by daac and instrument"""
    results = earthaccess.search_data(
        daac="NSIDC",
        instrument="atlas",
        count=expected_count,
        )
    assert len(results) > 0
