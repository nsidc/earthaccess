from unittest.mock import patch

import pytest
from earthaccess.dmrpp_zarr import get_granule_credentials_endpoint_and_region
from earthaccess.results import DataCollection, DataGranule

granule_no_credentials_endpoint = DataGranule(
    {
        "meta": {
            "collection-concept-id": "C1234-PROV",
        },
        "umm": {
            "RelatedUrls": [
                {
                    "URL": "https://data.earthdata.nasa.gov/data.h5",
                    "Type": "GET DATA",
                },
            ],
        },
    },
    cloud_hosted=True,
)


@patch("earthaccess.search_datasets")
def test_get_granule_credentials_and_region_from_granule(mock_search_datasets):
    """If credentials endpoint is populated in the granule it is used."""
    granule_credentials_endpoint = (
        "https://archive.daac.earthdata.nasa.gov/s3credentials"
    )
    granule = DataGranule(
        {
            "meta": {
                "collection-concept-id": "C1234-PROV",
            },
            "umm": {
                "RelatedUrls": [
                    {
                        "URL": "https://data.earthdata.nasa.gov/data.h5",
                        "Type": "GET DATA",
                    },
                    {
                        "URL": "s3://daac-cumulus-prod-protected/data.h5",
                        "Type": "GET DATA VIA DIRECT ACCESS",
                    },
                    {
                        "URL": granule_credentials_endpoint,
                        "Type": "VIEW RELATED INFORMATION",
                    },
                ],
            },
        },
        cloud_hosted=True,
    )

    # Credentials endpoint is retrieved from the granule, the region is set to
    # a default value of us-west-2.
    assert get_granule_credentials_endpoint_and_region(granule) == (
        granule_credentials_endpoint,
        "us-west-2",
    )

    # Ensure no attempt was made to retrieve collection information
    mock_search_datasets.assert_not_called()


@patch("earthaccess.search_datasets")
def test_get_granule_credentials_and_region_from_collection(mock_search_datasets):
    """If granule does not have credentials, those for a collection are retrieved."""
    collection_credentials_endpoint = (
        "https://archive.other-daac.earthdata.nasa.gov/s3credentials"
    )
    collection_region = "us-east-1"

    mock_search_datasets.return_value = [
        DataCollection(
            {
                "meta": {
                    "concept-id": "C1234-PROV",
                },
                "umm": {
                    "DirectDistributionInformation": {
                        "Region": collection_region,
                        "S3CredentialsAPIEndpoint": collection_credentials_endpoint,
                    },
                },
            }
        ),
    ]
    # Credentials endpoint is retrieved from the collection, the region is also
    # retrieved from the collection.
    assert get_granule_credentials_endpoint_and_region(
        granule_no_credentials_endpoint
    ) == (
        collection_credentials_endpoint,
        collection_region,
    )

    # An attempt was made to retrieve collection information
    mock_search_datasets.assert_called_once_with(count=1, concept_id="C1234-PROV")


@patch("earthaccess.search_datasets")
def test_get_granule_credentials_from_collection_default_region(mock_search_datasets):
    """If a collection does not have a region, the default of us-west-2 is used."""
    collection_credentials_endpoint = (
        "https://archive.other-daac.earthdata.nasa.gov/s3credentials"
    )

    mock_search_datasets.return_value = [
        DataCollection(
            {
                "meta": {
                    "concept-id": "C1234-PROV",
                },
                "umm": {
                    "DirectDistributionInformation": {
                        "S3CredentialsAPIEndpoint": collection_credentials_endpoint,
                    },
                },
            }
        ),
    ]
    # Credentials endpoint is retrieved from the collection, the region is also
    # retrieved from the collection.
    assert get_granule_credentials_endpoint_and_region(
        granule_no_credentials_endpoint
    ) == (
        collection_credentials_endpoint,
        "us-west-2",
    )

    # An attempt was made to retrieve collection information
    mock_search_datasets.assert_called_once_with(count=1, concept_id="C1234-PROV")


@patch("earthaccess.search_datasets")
def test_get_granule_credentials_no_collection_endpoint(mock_search_datasets):
    """Exception raised if a collection does not have an S3CredentialsAPIEndpoint."""
    mock_search_datasets.return_value = [
        DataCollection(
            {
                "meta": {
                    "concept-id": "C1234-PROV",
                },
                "umm": {
                    "DirectDistributionInformation": {
                        "Region": "us-east-1",
                    },
                },
            }
        ),
    ]
    # Credentials endpoint is retrieved from the collection, the region is also
    # retrieved from the collection.

    with pytest.raises(ValueError, match="did not provide an S3CredentialsAPIEndpoint"):
        get_granule_credentials_endpoint_and_region(granule_no_credentials_endpoint)

    # An attempt was made to retrieve collection information
    mock_search_datasets.assert_called_once_with(count=1, concept_id="C1234-PROV")
