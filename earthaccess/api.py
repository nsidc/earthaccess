from typing import Any, Dict, List, Optional, Type, Union

import earthaccess
import requests
import s3fs
from fsspec import AbstractFileSystem

from .auth import Auth
from .results import DataGranule
from .search import CollectionQuery, DataCollections, DataGranules, GranuleQuery
from .store import Store
from .utils import _validation as validate


def _normalize_location(location: Union[str, None]) -> Union[str, None]:
    """Handle user-provided `daac` and `provider` values

    These values must have a capital letter as the first character
    followed by capital letters, numbers, or an underscore. Here we
    uppercase all strings to handle the case when users provide
    lowercase values (e.g. "pocloud" instead of "POCLOUD").

    https://wiki.earthdata.nasa.gov/display/ED/CMR+Data+Partner+User+Guide?src=contextnavpagetreemode
    """
    if location is not None:
        location = location.upper()
    return location


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
            keyword="sea surface anomaly",
            cloud_hosted=True
        )
        ```
    """
    if not validate.valid_dataset_parameters(**kwargs):
        print(
            "Warning: a valid set of parameters is needed to search for datasets on CMR"
        )
        return []
    if earthaccess.__auth__.authenticated:
        query = DataCollections(auth=earthaccess.__auth__).parameters(**kwargs)
    else:
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
    if earthaccess.__auth__.authenticated:
        query = DataGranules(earthaccess.__auth__).parameters(**kwargs)
    else:
        query = DataGranules().parameters(**kwargs)
    granules_found = query.hits()
    print(f"Granules found: {granules_found}")
    if count > 0:
        return query.get(count)
    return query.get_all()


def login(strategy: str = "all", persist: bool = False) -> Auth:
    """Authenticate with Earthdata login (https://urs.earthdata.nasa.gov/)

    Parameters:

        strategy (String): authentication method.

                "all": (default) try all methods until one works

                "interactive": enter username and password.

                "netrc": retrieve username and password from ~/.netrc.

                "environment": retrieve username and password from $EARTHDATA_USERNAME and $EARTHDATA_PASSWORD.
        persist (Boolean): will persist credentials in a .netrc file
    Returns:
        an instance of Auth.
    """
    if strategy == "all":
        for strategy in ["environment", "netrc", "interactive"]:
            try:
                earthaccess.__auth__.login(strategy=strategy, persist=persist)
            except Exception:
                pass

            if earthaccess.__auth__.authenticated:
                earthaccess.__store__ = Store(earthaccess.__auth__)
                break
    else:
        earthaccess.__auth__.login(strategy=strategy, persist=persist)
        if earthaccess.__auth__.authenticated:
            earthaccess.__store__ = Store(earthaccess.__auth__)

    return earthaccess.__auth__


def download(
    granules: Union[DataGranule, List[DataGranule], str, List[str]],
    local_path: Union[str, None],
    provider: Optional[str] = None,
    threads: int = 8,
) -> List[str]:
    """Retrieves data granules from a remote storage system.

       * If we run this in the cloud, we will be using S3 to move data to `local_path`
       * If we run it outside AWS (us-west-2 region) and the dataset is cloud hostes we'll use HTTP links

    Parameters:
        granules: a granule, list of granules, a granule link (HTTP), or a list of granule links (HTTP)
        local_path: local directory to store the remote data granules
        provider: if we download a list of URLs we need to specify the provider.
        threads: parallel number of threads to use to download the files, adjust as necessary, default = 8

    Returns:
        List of downloaded files
    """
    provider = _normalize_location(provider)
    if isinstance(granules, DataGranule):
        granules = [granules]
    elif isinstance(granules, str):
        granules = [granules]
    try:
        results = earthaccess.__store__.get(granules, local_path, provider, threads)
    except AttributeError as err:
        print(err)
        print("You must call earthaccess.login() before you can download data")
        return []
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
    provider = _normalize_location(provider)
    results = earthaccess.__store__.open(granules=granules, provider=provider)
    return results


def get_s3_credentials(
    daac: Optional[str] = None,
    provider: Optional[str] = None,
    results: Optional[List[earthaccess.results.DataGranule]] = None,
) -> Dict[str, Any]:
    """Returns temporary (1 hour) credentials for direct access to NASA S3 buckets, we can
    use the daac name, the provider or a list of results from earthaccess.search_data()
    if we use results earthaccess will use the metadata on the response to get the credentials,
    this is useful for missions that do not use the same endpoint as their DAACs e.g. SWOT

    Parameters:
        daac (String): a DAAC short_name like NSIDC or PODAAC etc
        provider (String: if we know the provider for the DAAC e.g. POCLOUD, LPCLOUD etc.
        results (list[earthaccess.results.DataGranule]): List of results from search_data()
    Returns:
        a dictionary with S3 credentials for the DAAC or provider
    """
    daac = _normalize_location(daac)
    provider = _normalize_location(provider)
    if results is not None:
        endpoint = results[0].get_s3_credentials_endpoint()
        return earthaccess.__auth__.get_s3_credentials(endpoint=endpoint)
    return earthaccess.__auth__.get_s3_credentials(daac=daac, provider=provider)


def collection_query() -> Type[CollectionQuery]:
    """Returns a query builder instance for NASA collections (datasets)

    Parameters:
        cloud_hosted (Boolean): initializes the query builder for cloud hosted collections.
    Returns:
        class earthaccess.DataCollections: a query builder instance for data collections.
    """
    if earthaccess.__auth__.authenticated:
        query_builder = DataCollections(earthaccess.__auth__)
    else:
        query_builder = DataCollections()
    return query_builder


def granule_query() -> Type[GranuleQuery]:
    """Returns a query builder instance for data granules

    Parameters:
        cloud_hosted (Boolean): initializes the query builder for a particular DOI
        if we have it.
    Returns:
        class earthaccess.DataGranules: a query builder instance for data granules.
    """
    if earthaccess.__auth__.authenticated:
        query_builder = DataGranules(earthaccess.__auth__)
    else:
        query_builder = DataGranules()
    return query_builder


def get_fsspec_https_session() -> AbstractFileSystem:
    """Returns a fsspec session that can be used to access datafiles across many different DAACs

    Returns:
        class AbstractFileSystem: an fsspec instance able to access data across DAACs

    Examples:
        ```python
        import earthaccess

        earthaccess.login()
        fs = earthaccess.get_fsspec_https_session()
        with fs.open(DAAC_GRANULE) as f:
            f.read(10)
        ```

    """
    session = earthaccess.__store__.get_fsspec_session()
    return session


def get_requests_https_session() -> requests.Session:
    """Returns a requests Session instance with an authorized bearer token
    this is useful to make requests to restricted URLs like data granules or services that
    require authentication with NASA EDL.

    Returns:
        class requests.Session: an authenticated requests Session instance.

    Examples:
        ```python
        import earthaccess

        earthaccess.login()

        req_session = earthaccess.get_requests_https_session()
        data = req_session.get(granule_url, headers = {"Range": "bytes=0-100"})

        ```
    """
    session = earthaccess.__store__.get_requests_session()
    return session


def get_s3fs_session(
    daac: Optional[str] = None,
    provider: Optional[str] = None,
    results: Optional[earthaccess.results.DataGranule] = None,
) -> s3fs.S3FileSystem:
    """Returns a fsspec s3fs file session for direct access when we are in us-west-2

    Parameters:
        daac (String): Any DAAC short name e.g. NSIDC, GES_DISC
        provider (String): Each DAAC can have a cloud provider, if the DAAC is specified, there is no need to use provider
        results (list[class earthaccess.results.DataGranule]): A list of results from search_data(), earthaccess will use the metadata form CMR to obtain the S3 Endpoint

    Returns:
        class s3fs.S3FileSystem: an authenticated s3fs session valid for 1 hour
    """
    daac = _normalize_location(daac)
    provider = _normalize_location(provider)
    if results is not None:
        endpoint = results[0].get_s3_credentials_endpoint()
        if endpoint is not None:
            session = earthaccess.__store__.get_s3fs_session(endpoint=endpoint)
            return session
    session = earthaccess.__store__.get_s3fs_session(daac=daac, provider=provider)
    return session


def get_edl_token() -> str:
    """Returns the current token used for EDL

    Returns:
        str: EDL token

    """
    token = earthaccess.__auth__.token
    return token


def auth_environ() -> Dict[str, str]:
    auth = earthaccess.__auth__
    if not auth.authenticated:
        raise RuntimeError(
            "`auth_environ()` requires you to first authenticate with `earthaccess.login()`"
        )
    return {"EARTHDATA_USERNAME": auth.username, "EARTHDATA_PASSWORD": auth.password}
