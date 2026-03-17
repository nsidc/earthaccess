import pytest
from earthaccess.results import DataGranule

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
                    ]
                },
                {
                    "Points": [
                        {"Longitude": 2.8, "Latitude": 33.4},
                        {"Longitude": -9.2, "Latitude": 21.1},
                    ]
                },
            ]
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
            ]
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
                        ]
                    },
                },
            ]
        },
        "geojson": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-52.2, -45.3],
                        [-50.2, -40.3],
                        [-42.2, -35.3],
                    ]
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
                        ]
                    },
                    "ExclusiveZone": {
                        "Boundaries": [
                            {
                                "Points": [
                                    {"Longitude": -79.2, "Latitude": -40.1},
                                    {"Longitude": -70.8, "Latitude": -32.3},
                                    {"Longitude": -79.2, "Latitude": -32.3},
                                ]
                            },
                            {
                                "Points": [
                                    {"Longitude": 52.2, "Latitude": 25.3},
                                    {"Longitude": 54.2, "Latitude": 29.3},
                                    {"Longitude": 52.2, "Latitude": 29.3},
                                ]
                            },
                        ]
                    },
                },
            ]
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
                        ]
                    },
                },
                {
                    "Boundary": {
                        "Points": [
                            {"Longitude": -89.9, "Latitude": -40.3},
                            {"Longitude": 82.5, "Latitude": -40.3},
                            {"Longitude": 82.5, "Latitude": -45.9},
                            {"Longitude": -89.9, "Latitude": -40.3},
                        ]
                    },
                    "ExclusiveZone": {
                        "Boundaries": [
                            {
                                "Points": [
                                    {"Longitude": -79.2, "Latitude": -40.1},
                                    {"Longitude": -70.8, "Latitude": -32.3},
                                    {"Longitude": -79.2, "Latitude": -32.3},
                                ]
                            },
                            {
                                "Points": [
                                    {"Longitude": 52.2, "Latitude": 25.3},
                                    {"Longitude": 54.2, "Latitude": 29.3},
                                    {"Longitude": 52.2, "Latitude": 29.3},
                                ]
                            },
                        ]
                    },
                },
            ]
        },
        "geojson": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-52.2, -45.3],
                        [-50.2, -40.3],
                        [-42.2, -35.3],
                    ]
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
        {"umm": {"SpatialExtent": {"HorizontalSpatialDomain": {"Geometry": geometry}}}}
    )

    assert granule.__geo_interface__ == geojson


def test_missing_horizontal_spatial_domain_raises():
    granule = DataGranule({"umm": {"SpatialExtent": {"Orbit": {}}}})

    with pytest.raises(ValueError):
        granule.__geo_interface__
