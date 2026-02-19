"""Tests for search_data.  This needs a mock to be set up but for now, I get all
the first 10 granules using count=10.
"""

import earthaccess
import pytest

# Set SKIP_THIS to False to run test
SKIP_THIS = True

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

# Polygon over Jakobshavn Isbrae
polygon = [
    (-49.64860422604741, 69.23553485026147),
    (-49.667876114626296, 69.07309059285959),
    (-49.1722491331669, 69.03175841820749),
    (-47.53552489113113, 69.03872918462292),
    (-47.35616491854395, 69.22149993224824),
    (-48.1447695277283, 69.33507802083219),
    (-49.178671242118384, 69.29455117736225),
    (-49.64860422604741, 69.23553485026147),
]

# Canyon de Chelly, Az (Near Chinle, Naabeehó Bináhásdzo)
line = [
    (-109.49099495904196, 36.141620186146454),
    (-109.46326273316441, 36.12549319389707),
    (-109.42416829289516, 36.11336807764218),
    (-109.39942951589708, 36.10816134722084),
    (-109.33995221922424, 36.10943400693182),
    (-109.28600071040317, 36.11941578661717),
]

# Taos, NM
circle = (-105.61708725711999, 36.38510879364757, 1000.0)


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_shortname():
    """Tests granule search by short name returns
    results that match expected_count.
    """
    results = earthaccess.search_data(short_name=short_name, count=expected_count)
    assert len(results) == expected_count


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_with_version():
    """Tests granule search by short name and version.
    returned expected_count.
    """
    results = earthaccess.search_data(
        short_name=short_name, version=version, count=expected_count
    )
    assert len(results) == expected_count


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_provider():
    """Tests granule search by provider returns
    expected_count.
    """
    results = earthaccess.search_data(
        provider=provider,
        count=expected_count,
    )
    assert len(results) == expected_count


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_daac():
    """Tests granule search by daac returns
    expected_count.
    """
    results = earthaccess.search_data(
        daac=daac,
        count=expected_count,
    )
    assert len(results) == expected_count


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_data_center():
    """Tests granule search by data_center returns
    expected_count.
    """
    results = earthaccess.search_data(
        data_center=data_center,
        count=expected_count,
    )
    assert len(results) == expected_count


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_coud_hosted():
    """Tests granule search by short_name with only
    cloud_hosted granules.
    """
    results = earthaccess.search_data(
        short_name=short_name,
        cloud_hosted=True,
        count=expected_count,
    )
    assert len(results) == expected_count


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_online_only():
    """Tests granule search by short_name with online
    only granules.
    """
    results = earthaccess.search_data(
        short_name=short_name,
        online_only=True,
        count=expected_count,
    )
    assert len(results) == expected_count


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_downloadable():
    """Tests granule search by short_name with downloadable
    granules.

    A granule is downloadable when it contains at least one RelatedURL of type GETDATA.
    """
    results = earthaccess.search_data(
        short_name=short_name,
        downloadable=True,
        count=expected_count,
    )
    assert len(results) == expected_count


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_orbit_number():
    """Tests granule search by short_name with orbit_number."""
    results = earthaccess.search_data(
        short_name=short_name,
        orbit_number=orbit_number,
        count=expected_count,
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_granule_name():
    """Tests granule search by short_name and granule name."""
    results = earthaccess.search_data(
        short_name=short_name,
        granule_name=granule_name,
    )
    assert len(results) == 1


# day_night_flag returns 0 granules
@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_day_night_flag():
    """Tests granule search by short_name and granule name."""
    results = earthaccess.search_data(
        short_name="MOD10A1", day_night_flag="Day", count=expected_count
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_daac_with_instrument():
    """Test search_data by daac and instrument."""
    results = earthaccess.search_data(
        daac="NSIDC",
        instrument="modis",
        count=expected_count,
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_daac_with_platform():
    """Test search_data by daac and platform."""
    results = earthaccess.search_data(
        daac="NSIDC",
        platform="terra",
        count=expected_count,
    )
    assert len(results) > 0


@pytest.mark.skip(reason="unable to build useful test")
def test_search_data_by_short_name_with_cloud_cover():
    """Test search_data by short_name and cloud cover."""
    results = earthaccess.search_data(
        short_name="MOD10A1",
        cloud_cover=(0, 50),
        count=10,
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_bounding_box():
    """Tests searching for granules with bounding box."""
    results = earthaccess.search_data(
        short_name="ATL06",
        bounding_box=(-46.5, 61.0, -42.5, 63.0),
        count=expected_count,
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_polygon():
    """Tests searching for granules with polygon."""
    results = earthaccess.search_data(
        short_name="ATL06",
        polygon=polygon,
        count=expected_count,
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_point():
    """Tests searching for granules with point."""
    results = earthaccess.search_data(
        short_name="MOD10A1",
        point=(-105.61708725711999, 36.38510879364757),
        count=10,
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_circle():
    """Tests searching for granules with circle."""
    results = earthaccess.search_data(
        short_name="ATL03",
        circle=circle,
        count=expected_count,
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_line():
    """Tests searching for granules with line."""
    results = earthaccess.search_data(
        short_name="ATL08",
        line=line,
        count=expected_count,
    )
    assert len(results) > 0


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_multipoint():
    """Tests searching for granules with multiple points."""
    # Test with 2 points
    multipoint_coords = [
        (-105.61708725711999, 36.38510879364757),  # Taos, NM
        (-112.73, 42.5),  # Idaho/Utah area
    ]
    results = earthaccess.search_data(
        short_name="MOD10A1",
        multipoint=multipoint_coords,
        count=expected_count,
    )
    assert len(results) > 0
    
    # Verify that multipoint returns more results than single point
    single_point_results = earthaccess.search_data(
        short_name="MOD10A1",
        point=multipoint_coords[0],
        count=expected_count,
    )
    # Note: multipoint uses OR logic, so should generally return >= single point results
    assert len(results) >= len(single_point_results)


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_multipolygon():
    """Tests searching for granules with multiple polygons."""
    # Second polygon near Greenland
    polygon2 = [
        (-45.0, 70.0),
        (-45.0, 68.0),
        (-40.0, 68.0),
        (-40.0, 70.0),
        (-45.0, 70.0),
    ]
    
    multipolygon_coords = [polygon, polygon2]
    
    results = earthaccess.search_data(
        short_name="ATL06",
        multipolygon=multipolygon_coords,
        count=expected_count,
    )
    assert len(results) > 0
    
    # Verify that multipolygon returns more results than single polygon
    single_polygon_results = earthaccess.search_data(
        short_name="ATL06",
        polygon=polygon,
        count=expected_count,
    )
    # Note: multipolygon uses OR logic, so should generally return >= single polygon results
    assert len(results) >= len(single_polygon_results)


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_multi_bounding_box():
    """Tests searching for granules with multiple bounding boxes."""
    # Greenland area bounding boxes
    bbox1 = (-46.5, 61.0, -42.5, 63.0)  # Original bbox from existing test
    bbox2 = (-50.0, 65.0, -45.0, 68.0)  # Another Greenland area
    
    multi_bboxes = [bbox1, bbox2]
    
    results = earthaccess.search_data(
        short_name="ATL06",
        multi_bounding_box=multi_bboxes,
        count=expected_count,
    )
    assert len(results) > 0
    
    # Verify that multi_bounding_box returns more results than single bbox
    single_bbox_results = earthaccess.search_data(
        short_name="ATL06",
        bounding_box=bbox1,
        count=expected_count,
    )
    # Note: multi_bounding_box uses OR logic, so should generally return >= single bbox results
    assert len(results) >= len(single_bbox_results)


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_multiline():
    """Tests searching for granules with multiple lines."""
    # Second line in a different area
    line2 = [
        (-120.0, 40.0),
        (-119.0, 41.0),
        (-118.0, 42.0),
        (-117.0, 43.0),
    ]
    
    multiline_coords = [line, line2]
    
    results = earthaccess.search_data(
        short_name="ATL08",
        multiline=multiline_coords,
        count=expected_count,
    )
    assert len(results) > 0
    
    # Verify that multiline returns more results than single line
    single_line_results = earthaccess.search_data(
        short_name="ATL08",
        line=line,
        count=expected_count,
    )
    # Note: multiline uses OR logic, so should generally return >= single line results
    assert len(results) >= len(single_line_results)


@pytest.mark.skipif(SKIP_THIS, reason="calls python-cmr, set SKIP_THIS=False to run")
def test_search_data_by_short_name_with_multicircle():
    """Tests searching for granules with multiple circles."""
    # Define two circles
    circle1 = (-105.61708725711999, 36.38510879364757, 1000.0)  # Taos, NM
    circle2 = (-110.0, 35.0, 1500.0)  # Another area
    
    multicircle_coords = [circle1, circle2]
    
    results = earthaccess.search_data(
        short_name="ATL03",
        multicircle=multicircle_coords,
        count=expected_count,
    )
    assert len(results) > 0
    
    # Verify that multicircle returns more results than single circle
    single_circle_results = earthaccess.search_data(
        short_name="ATL03",
        circle=circle1,
        count=expected_count,
    )
    # Note: multicircle uses OR logic, so should generally return >= single circle results
    assert len(results) >= len(single_circle_results)
