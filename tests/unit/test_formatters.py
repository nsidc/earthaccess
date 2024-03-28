from earthaccess.formatters import (
    STATIC_FILES,
    _load_static_files,
    _repr_granule_html,
)
from earthaccess.results import DataGranule


def test_load_static_files():
    # We simply test that the number of static files loaded is the same as the
    # number of files in the STATIC_FILES list.  If we were to add logic to
    # check the contents of the files, then we would end up duplicating the
    # logic in the _load_static_files function, which wouldn't make sense to do.
    # If _load_static_files contains a bug, then this test will likely fail due
    # to the function raising an exception.
    assert len(_load_static_files()) == len(STATIC_FILES)


def test_repr_granule_html():
    static_contents = _load_static_files()
    size1 = 128573
    size2 = 2713600
    umm = {
        "RelatedUrls": [
            {
                "URL": "https://data.csdap.earthdata.nasa.gov/data.h5",
                "Type": "GET DATA",
            },
            {
                "URL": "s3://csda-cumulus-prod-protected-5047/data.h5",
                "Type": "GET DATA VIA DIRECT ACCESS",
            },
            {
                "URL": "https://data.csdap.earthdata.nasa.gov/thumb.jpg",
                "Type": "GET RELATED VISUALIZATION",
            },
        ],
        "DataGranule": {
            "ArchiveAndDistributionInformation": [
                {"SizeInBytes": size1},
                {"SizeInBytes": size2},
            ],
        },
    }

    html = _repr_granule_html(DataGranule({"umm": umm}, cloud_hosted=True))

    assert f"{round((size1 + size2) / 1024 / 1024, 2)} MB" in html
    assert [url["URL"] in html for url in umm["RelatedUrls"]] == [True, False, True]
    assert all(content in html for content in static_contents)
