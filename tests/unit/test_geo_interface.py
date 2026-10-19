import pytest
from earthaccess.results import DataCollection, DataGranule
from earthaccess.search import DataCollections, DataGranules

# Mapping from test case identifier to UMMG Geometry with the GeoJSON expected
# to be the value of the __geo_interface__ property of a DataGranule that
# contains the geometry in its horizontal spatial domain.
TEST_CASES = {
    "points": {
        "geometry": {
            "Points": [
                {"Longitude": -89.9, "Latitude": -40.3},
                {"Longitude": 82.5, "Latitude": -40.3},
                {"Longitude": 82.5, "Latitude": -45.9},
                {"Longitude": -89.9, "Latitude": -40.3},
            ],
        },
        "geojson": {
            "type": "MultiPoint",
            "coordinates": [
                [-89.9, -40.3],
                [82.5, -40.3],
                [82.5, -45.9],
                [-89.9, -40.3],
            ],
        },
    },
    "lines": {
        "geometry": {
            "Lines": [
                {
                    "Points": [
                        {"Longitude": -10.5, "Latitude": -20.9},
                        {"Longitude": 1.5, "Latitude": 5.6},
                        {"Longitude": 13.9, "Latitude": 15.6},
                    ],
                },
                {
                    "Points": [
                        {"Longitude": 2.8, "Latitude": 33.4},
                        {"Longitude": -9.2, "Latitude": 21.1},
                    ],
                },
            ],
        },
        "geojson": {
            "type": "MultiLineString",
            "coordinates": [
                [[-10.5, -20.9], [1.5, 5.6], [13.9, 15.6]],
                [[2.8, 33.4], [-9.2, 21.1]],
            ],
        },
    },
    "bounding-rectangles": {
        "geometry": {
            "BoundingRectangles": [
                {
                    "WestBoundingCoordinate": -43.2,
                    "SouthBoundingCoordinate": -10.1,
                    "EastBoundingCoordinate": 30.4,
                    "NorthBoundingCoordinate": 15.5,
                },
                {
                    "WestBoundingCoordinate": 22.3,
                    "SouthBoundingCoordinate": -33.3,
                    "EastBoundingCoordinate": 99.2,
                    "NorthBoundingCoordinate": 30.3,
                },
            ],
        },
        "geojson": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-43.2, -10.1],
                        [30.4, -10.1],
                        [30.4, 15.5],
                        [-43.2, 15.5],
                        [-43.2, -10.1],
                    ],
                ],
                [
                    [
                        [22.3, -33.3],
                        [99.2, -33.3],
                        [99.2, 30.3],
                        [22.3, 30.3],
                        [22.3, -33.3],
                    ],
                ],
            ],
        },
    },
    "single-gpolygon-without-exclusive-zone": {
        "geometry": {
            "GPolygons": [
                {
                    "Boundary": {
                        "Points": [
                            {"Longitude": -52.2, "Latitude": -45.3},
                            {"Longitude": -50.2, "Latitude": -40.3},
                            {"Longitude": -42.2, "Latitude": -35.3},
                        ],
                    },
                },
            ],
        },
        "geojson": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-52.2, -45.3],
                        [-50.2, -40.3],
                        [-42.2, -35.3],
                    ],
                ],
            ],
        },
    },
    "single-gpolygon-with-exclusive-zone": {
        "geometry": {
            "GPolygons": [
                {
                    "Boundary": {
                        "Points": [
                            {"Longitude": -89.9, "Latitude": -40.3},
                            {"Longitude": 82.5, "Latitude": -40.3},
                            {"Longitude": 82.5, "Latitude": -45.9},
                            {"Longitude": -89.9, "Latitude": -40.3},
                        ],
                    },
                    "ExclusiveZone": {
                        "Boundaries": [
                            {
                                "Points": [
                                    {"Longitude": -79.2, "Latitude": -40.1},
                                    {"Longitude": -70.8, "Latitude": -32.3},
                                    {"Longitude": -79.2, "Latitude": -32.3},
                                ],
                            },
                            {
                                "Points": [
                                    {"Longitude": 52.2, "Latitude": 25.3},
                                    {"Longitude": 54.2, "Latitude": 29.3},
                                    {"Longitude": 52.2, "Latitude": 29.3},
                                ],
                            },
                        ],
                    },
                },
            ],
        },
        "geojson": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-89.9, -40.3],
                        [82.5, -40.3],
                        [82.5, -45.9],
                        [-89.9, -40.3],
                    ],
                    [
                        # These are reversed to be clockwise, but we're not
                        # validating whether or not the original points are
                        # in counterclockwise order.
                        [-79.2, -32.3],
                        [-70.8, -32.3],
                        [-79.2, -40.1],
                    ],
                    [
                        # These are reversed to be clockwise, but we're not
                        # validating whether or not the original points are
                        # in counterclockwise order.
                        [52.2, 29.3],
                        [54.2, 29.3],
                        [52.2, 25.3],
                    ],
                ],
            ],
        },
    },
    "multiple-gpolygons": {
        "geometry": {
            "GPolygons": [
                {
                    "Boundary": {
                        "Points": [
                            {"Longitude": -52.2, "Latitude": -45.3},
                            {"Longitude": -50.2, "Latitude": -40.3},
                            {"Longitude": -42.2, "Latitude": -35.3},
                        ],
                    },
                },
                {
                    "Boundary": {
                        "Points": [
                            {"Longitude": -89.9, "Latitude": -40.3},
                            {"Longitude": 82.5, "Latitude": -40.3},
                            {"Longitude": 82.5, "Latitude": -45.9},
                            {"Longitude": -89.9, "Latitude": -40.3},
                        ],
                    },
                    "ExclusiveZone": {
                        "Boundaries": [
                            {
                                "Points": [
                                    {"Longitude": -79.2, "Latitude": -40.1},
                                    {"Longitude": -70.8, "Latitude": -32.3},
                                    {"Longitude": -79.2, "Latitude": -32.3},
                                ],
                            },
                            {
                                "Points": [
                                    {"Longitude": 52.2, "Latitude": 25.3},
                                    {"Longitude": 54.2, "Latitude": 29.3},
                                    {"Longitude": 52.2, "Latitude": 29.3},
                                ],
                            },
                        ],
                    },
                },
            ],
        },
        "geojson": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-52.2, -45.3],
                        [-50.2, -40.3],
                        [-42.2, -35.3],
                    ],
                ],
                [
                    [
                        [-89.9, -40.3],
                        [82.5, -40.3],
                        [82.5, -45.9],
                        [-89.9, -40.3],
                    ],
                    [
                        # These are reversed to be clockwise, but we're not
                        # validating whether or not the original points are
                        # in counterclockwise order.
                        [-79.2, -32.3],
                        [-70.8, -32.3],
                        [-79.2, -40.1],
                    ],
                    [
                        # These are reversed to be clockwise, but we're not
                        # validating whether or not the original points are
                        # in counterclockwise order.
                        [52.2, 29.3],
                        [54.2, 29.3],
                        [52.2, 25.3],
                    ],
                ],
            ],
        },
    },
}


@pytest.mark.parametrize("test_case", TEST_CASES.values(), ids=TEST_CASES.keys())
def test_geo_interface(test_case: dict[str, object]):
    geometry = test_case["geometry"]
    geojson = test_case["geojson"]
    granule = DataGranule(
        {"umm": {"SpatialExtent": {"HorizontalSpatialDomain": {"Geometry": geometry}}}},
    )

    assert granule.__geo_interface__ == geojson


def test_missing_horizontal_spatial_domain_raises():
    granule = DataGranule({"umm": {"SpatialExtent": {"Orbit": {}}}})

    with pytest.raises(ValueError):
        _ = granule.__geo_interface__


def _make_granule(test_case: dict[str, object], name: str) -> DataGranule:
    """Returns a DataGranule with geometry and key attributes for testing to_geopandas()."""
    return DataGranule(
        {
            "meta": {"concept-id": f"G-{name}", "provider-id": "PROV"},
            "umm": {
                "GranuleUR": name,
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {"Geometry": test_case["geometry"]},
                },
                "TemporalExtent": {
                    "RangeDateTime": {
                        "BeginningDateTime": "2024-01-01T00:00:00.000Z",
                        "EndingDateTime": "2024-01-02T23:59:59.000Z",
                    },
                },
                "RelatedUrls": [
                    {
                        "URL": f"https://data.ornldaac.nasa.gov/protected/{name}.nc",
                        "Type": "GET DATA",
                        "Description": f"Download {name}.nc",
                    },
                ],
            },
        },
    )


def test_to_geopandas_returns_geodataframe():
    gpd = pytest.importorskip("geopandas")

    granules = [
        _make_granule(TEST_CASES["multiple-gpolygons"], "poly"),
        _make_granule(TEST_CASES["points"], "point"),
        _make_granule(TEST_CASES["lines"], "line"),
    ]

    gdf = DataGranules.to_geopandas(granules)

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert str(gdf.crs).upper() == "EPSG:4326"
    assert len(gdf) == 3
    assert list(gdf.geometry.geom_type) == [
        "MultiPolygon",
        "MultiPoint",
        "MultiLineString",
    ]
    assert gdf.geometry.notna().all()


def test_to_geopandas_includes_attribute_columns():
    pytest.importorskip("geopandas")

    granules = [_make_granule(TEST_CASES["bounding-rectangles"], "rect")]
    gdf = DataGranules().to_geopandas(granules)

    row = gdf.iloc[0]
    assert row["concept_id"] == "G-rect"
    assert row["granule_name"] == "rect"
    assert row["beginning_datetime"] == "2024-01-01T00:00:00.000Z"
    assert row["ending_datetime"] == "2024-01-02T23:59:59.000Z"
    assert row["data_links"] == ["https://data.ornldaac.nasa.gov/protected/rect.nc"]
    assert "size_MB" in gdf.columns


def test_to_geopandas_includes_full_umm_column():
    pytest.importorskip("geopandas")

    granule = _make_granule(TEST_CASES["points"], "point")
    gdf = DataGranules().to_geopandas([granule])

    row = gdf.iloc[0]
    assert row["umm.GranuleUR"] == granule["umm"]["GranuleUR"]
    assert (
        row["umm.SpatialExtent.HorizontalSpatialDomain.Geometry.Points"]
        == TEST_CASES["points"]["geometry"]["Points"]
    )


def test_to_geopandas_keeps_granules_without_spatial_extent():
    pytest.importorskip("geopandas")

    with_geom = _make_granule(TEST_CASES["points"], "point")
    without_geom = DataGranule(
        {
            "meta": {"concept-id": "G-nospatial"},
            "umm": {"GranuleUR": "nospatial", "SpatialExtent": {"Orbit": {}}},
        },
    )
    gdf = DataGranules().to_geopandas([with_geom, without_geom])
    assert len(gdf) == 2
    assert gdf.geometry.iloc[0] is not None
    assert gdf.geometry.iloc[1] is None
    assert gdf["concept_id"].tolist() == ["G-point", "G-nospatial"]


def test_to_geopandas_empty_result():
    pytest.importorskip("geopandas")
    gdf = DataGranules().to_geopandas([])
    assert len(gdf) == 0


def _make_collection(test_case: dict[str, object], name: str) -> DataCollection:
    """Returns a DataCollection with geometry and key attributes for testing to_geopandas()."""
    return DataCollection(
        {
            "meta": {"concept-id": f"C-{name}", "provider-id": "PROV"},
            "umm": {
                "ShortName": name,
                "Version": "2.1",
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {"Geometry": test_case["geometry"]},
                },
                "EntryTitle": name,
                "DOI": {"DOI": "10.3334/ORNLDAAC/146", "Authority": "https://doi.org"},
            },
        },
    )


def test_collections_to_geopandas_returns_geodataframe():
    gpd = pytest.importorskip("geopandas")
    collections = [
        _make_collection(TEST_CASES["bounding-rectangles"], "coll-rect"),
        _make_collection(TEST_CASES["multiple-gpolygons"], "coll-poly"),
        _make_collection(TEST_CASES["points"], "coll-point"),
    ]
    gdf = DataCollections.to_geopandas(collections)

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert str(gdf.crs).upper() == "EPSG:4326"
    assert len(gdf) == 3
    assert list(gdf.geometry.geom_type) == [
        "MultiPolygon",
        "MultiPolygon",
        "MultiPoint",
    ]
    assert gdf.geometry.notna().all()


def test_collections_to_geopandas_includes_attribute_columns():
    pytest.importorskip("geopandas")
    collection = _make_collection(TEST_CASES["bounding-rectangles"], "coll-rect")
    gdf = DataCollections.to_geopandas([collection])

    row = gdf.iloc[0]
    assert row["concept_id"] == "C-coll-rect"
    assert row["short_name"] == "coll-rect"
    assert row["version"] == "2.1"
    assert row["title"] == "coll-rect"
    assert row["doi"] == "10.3334/ORNLDAAC/146"


def test_collections_to_geopandas_includes_full_umm_column():
    pytest.importorskip("geopandas")

    collection = _make_collection(TEST_CASES["points"], "coll-point")
    gdf = DataCollections.to_geopandas([collection])
    row = gdf.iloc[0]
    assert row["umm.ShortName"] == collection["umm"]["ShortName"]
    assert (
        row["umm.SpatialExtent.HorizontalSpatialDomain.Geometry.Points"]
        == TEST_CASES["points"]["geometry"]["Points"]
    )


def test_collections_to_geopandas_keeps_collections_without_spatial_extent():
    pytest.importorskip("geopandas")

    with_geom = _make_collection(TEST_CASES["points"], "coll-point")
    without_geom = DataCollection(
        {
            "meta": {"concept-id": "C-nospatial"},
            "umm": {"ShortName": "nospatial", "SpatialExtent": {}},
        },
    )

    gdf = DataCollections.to_geopandas([with_geom, without_geom])
    assert len(gdf) == 2
    assert gdf.geometry.iloc[0] is not None
    assert gdf.geometry.iloc[1] is None
    assert gdf["concept_id"].tolist() == ["C-coll-point", "C-nospatial"]


def test_collections_to_geopandas_empty_result():
    pytest.importorskip("geopandas")

    gdf = DataCollections.to_geopandas([])
    assert len(gdf) == 0
