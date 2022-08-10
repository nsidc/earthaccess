# package imports
from earthdata.search import DataCollections


def test_query_can_find_cloud_provider():
    query = DataCollections().daac("PODAAC").cloud_hosted(True)
    assert query.params["provider"] == "POCLOUD"
    query = DataCollections().cloud_hosted(True).daac("PODAAC")
    assert query.params["provider"] == "POCLOUD"
    # OBDAAC does not have a cloud provider so it should default to the on prem provider
    query = DataCollections().cloud_hosted(True).daac("OBDAAC")
    assert query.params["provider"] == "OB_DAAC"
