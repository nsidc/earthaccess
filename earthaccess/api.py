from typing import Any, Dict, List, Optional, Union

from fsspec import AbstractFileSystem

import earthaccess

from .auth import Auth
from .search import DataCollections, DataGranules
from .store import Store
from .utils import _validation as validate


def search_datasets(
    count: int = -1, **kwargs: Any
) -> List[earthaccess.results.DataCollection]:
    """Search datasets using NASA's CMR

    [https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)

    Parameters:

        count (Integer): Number of records to get, -1 = all
        kwargs (Dict): arguments to CMR:

            * **keyword**: case insensitive and support wild cards ? and *,

            * **short_name**: e.g. ATL08

            * **doi**: DOI for a dataset

            * **daac**: e.g. NSIDC or PODAAC

            * **provider**: particular to each DAAC, e.g. POCLOUD, LPDAAC etc.

            * **temporal**: ("yyyy-mm-dd", "yyyy-mm-dd")

            * **bounding_box**: (lower_left_lon, lower_left_lat ,
                               upper_right_lon, upper_right_lat)
    Returns:
        an list of DataCollection results that can be used to get
        information such as concept_id, doi, etc. about a dataset.
    Examples:
        ```python
        datasets = earthaccess.search_datasets(
            keywords="sea surface anomaly",
            cloud_hosted=True
        )
        ```
    """
    if not validate.valid_dataset_parameters(**kwargs):
        print(
            "Warning: a valid set of parameters is needed to search for datasets on CMR"
        )
        return []
    query = DataCollections().parameters(**kwargs)
    datasets_found = query.hits()
    print(f"Datasets found: {datasets_found}")
    if count > 0:
        return query.get(count)
    return query.get_all()


def search_data(
    count: int = -1, **kwargs: Any
) -> List[earthaccess.results.DataGranule]:
    """Search dataset granules using NASA's CMR.

    [https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)

    Parameters:

        count (Integer): Number of records to get, -1 = all
        kwargs (Dict): arguments to CMR:

            * **short_name**: dataset short name e.g. ATL08

            * **version**: dataset version

            * **doi**: DOI for a dataset

            * **daac**: e.g. NSIDC or PODAAC

            * **provider**: particular to each DAAC, e.g. POCLOUD, LPDAAC etc.

            * **temporal**: ("yyyy-mm-dd", "yyyy-mm-dd")

            * **bounding_box**: (lower_left_lon, lower_left_lat ,
                               upper_right_lon, upper_right_lat)
    Returns:
        Granules: a list of DataGranules that can be used to access
          the granule files by using `download()` or `open()`.
    Examples:
        ```python
        datasets = earthaccess.search_data(
            doi="10.5067/SLREF-CDRV2",
            cloud_hosted=True,
            temporal=("2002-01-01", "2002-12-31")
        )
        ```
    """
    query = DataGranules().parameters(**kwargs)
    granules_found = query.hits()
    print(f"Granules found: {granules_found}")
    if count > 0:
        return query.get(count)
    return query.get_all()


def login(strategy: str = "interactive") -> Auth:
    """Authenticate with Earthdata login (https://urs.earthdata.nasa.gov/)

    Parameters:

        strategy (String): authentication method.

                "interactive": (default) enter username and password.

                "netrc": retrieve username and password from ~/.netrc.

                "environment": retrieve username and password from $EDL_USERNAME and $EDL_PASSWORD.
        persist (Boolean): will persist credentials in a .netrc file
    Returns:
        an instance of Auth.
    """
    earthaccess.__auth__.login(strategy=strategy)
    earthaccess.__store__ = Store(earthaccess.__auth__)
    return earthaccess.__auth__


def download(
    granules: Union[List[earthaccess.results.DataGranule], List[str]],
    local_path: Optional[str],
    provider: Optional[str] = None,
    threads: int = 8,
) -> List[str]:
    """Retrieves data granules from a remote storage system.

       * If we run this in the cloud, we will be using S3 to move data to `local_path`
       * If we run it outside AWS (us-west-2 region) and the dataset is cloud hostes we'll use HTTP links

    Parameters:
        granules: a list of granules(DataGranule) instances or a list of granule links (HTTP)
        local_path: local directory to store the remote data granules
        provider: if we download a list of URLs we need to specify the provider.
        threads: parallel number of threads to use to download the files, adjust as necessary, default = 8

    Returns:
        List of downloaded files
    """
    results = earthaccess.__store__.get(granules, local_path, provider, threads)
    return results


def open(
    granules: Union[List[str], List[earthaccess.results.DataGranule]],
    provider: Optional[str] = None,
) -> List[AbstractFileSystem]:
    """Returns a list of fsspec file-like objects that can be used to access files
    hosted on S3 or HTTPS by third party libraries like xarray.

    Parameters:
        granules: a list of granule instances **or** list of URLs, e.g. s3://some-granule,
        if a list of URLs is passed we need to specify the data provider e.g. POCLOUD, NSIDC_CPRD etc.
    Returns:
        a list of s3fs "file pointers" to s3 files.
    """
    results = earthaccess.__store__.open(granules, provider)
    return results


def get_s3_credentials(daac: str, provider: str) -> Dict[str, Any]:
    return {}
