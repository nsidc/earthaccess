import geopandas as gpd

COUNT = 10


def _get_granules(collection: str):
    import earthaccess

    earthaccess.login()

    return earthaccess.search_data(short_name=collection, count=COUNT)


def _check_geoms(geoms: gpd.GeoSeries):
    assert len(geoms) == COUNT
    assert geoms.is_valid.all()


def test_geo_gpolygons():
    granules = _get_granules("MYD11A1")
    geoms = gpd.GeoSeries(granules, crs=4326)
    _check_geoms(geoms)
    assert (geoms.geom_type == "MultiPolygon").all()


def test_geo_bounding_rects():
    granules = _get_granules("SRTMGL1")
    geoms = gpd.GeoSeries(granules, crs=4326)
    _check_geoms(geoms)
    assert (geoms.geom_type == "MultiPolygon").all()


def test_geo_points():
    granules = _get_granules("SNEX23_MAR23_SP")
    geoms = gpd.GeoSeries(granules, crs=4326)
    _check_geoms(geoms)
    assert (geoms.geom_type == "MultiPoint").all()


def test_geo_linestrings():
    granules = _get_granules("JASON_3_L2_OST_OGDR_GPS")
    geoms = gpd.GeoSeries(granules, crs=4326)
    _check_geoms(geoms)
    assert (geoms.geom_type == "MultiLineString").all()
