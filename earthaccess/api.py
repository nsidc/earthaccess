import logging
from pathlib import Path

import requests
import s3fs
from fsspec import AbstractFileSystem
from typing_extensions import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Union,
    deprecated,
)

import earthaccess
from earthaccess.exceptions import LoginStrategyUnavailable
from earthaccess.services import DataServices

from .auth import Auth
from .results import DataCollection, DataGranule
from .search import CollectionQuery, DataCollections, DataGranules, GranuleQuery
from .store import Store
from .system import PROD, UAT, System
from .utils import _validation as validate

logger = logging.getLogger(__name__)


def status(system: System = PROD) -> Mapping[str, str]:
    """Gets the status of NASA's Earthdata services.

    Parameters:
        system: The Earthdata system to access, defaults to PROD.

    Returns:
        A dictionary containing the status of Earthdata services.

    Examples:
        >>> earthaccess.status()  # doctest: +SKIP
        {'Earthdata Login': 'OK', 'Common Metadata Repository': 'OK'}
        >>> earthaccess.status(earthaccess.UAT)  # doctest: +SKIP
        {'Earthdata Login': 'OK', 'Common Metadata Repository': 'OK'}
    """
    urls = {
        PROD: "https://status.earthdata.nasa.gov/api/v1/statuses",
        UAT: "https://status.uat.earthdata.nasa.gov/api/v1/statuses",
    }
    earthdata_services = ["Earthdata Login", "Common Metadata Repository"]
    url = urls[system]

    try:
        response = requests.get(url)
        result = {}

        for status in response.json()["statuses"]:
            name = status["name"]
            if name.endswith("(UAT)"):
                name = name.replace("(UAT)", "").strip()
            elif name.endswith("(PROD)"):
                name = name.replace("(PROD)", "").strip()

            if name in earthdata_services:
                result[name] = status["status"]

        return result

    except Exception as e:
        logger.error(f"Failed to retrieve Earthdata service status for {system}: {e}")
        return None


def _normalize_location(location: Optional[str]) -> Optional[str]:
    """Handle user-provided `daac` and `provider` values.

    These values must have a capital letter as the first character
    followed by capital letters, numbers, or an underscore. Here we
    uppercase all strings to handle the case when users provide
    lowercase values (e.g. "pocloud" instead of "POCLOUD").

    https://wiki.earthdata.nasa.gov/display/ED/CMR+Data+Partner+User+Guide?src=contextnavpagetreemode
    """
    if location is not None:
        location = location.upper()
    return location


def search_datasets(count: int = -1, **kwargs: Any) -> List[DataCollection]:
    """Search datasets using NASA's CMR.

    [https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)

    Parameters:
        count: Number of records to get, -1 = all
        kwargs (Dict):
            arguments to CMR:

            * **keyword**: case-insensitive and supports wildcards ? and *
            * **short_name**: e.g. ATL08
            * **doi**: DOI for a dataset
            * **daac**: e.g. NSIDC or PODAAC
            * **provider**: particular to each DAAC, e.g. POCLOUD, LPDAAC etc.
            * **has_granules**: if true, only return collections with granules
            * **temporal**: a tuple representing temporal bounds in the form
              `(date_from, date_to)`
            * **bounding_box**: a tuple representing spatial bounds in the form
              `(lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)`

    Returns:
        A list of DataCollection results that can be used to get information about a
            dataset, e.g. concept_id, doi, etc.

    Raises:
        RuntimeError: The CMR query failed.

    Examples:
        ```python
        datasets = earthaccess.search_datasets(
            keyword="sea surface anomaly",
            cloud_hosted=True
        )
        ```
    """
    if not validate.valid_dataset_parameters(**kwargs):
        logger.warning(
            "A valid set of parameters is needed to search for datasets on CMR"
        )
        return []
    if earthaccess.__auth__.authenticated:
        query = DataCollections(auth=earthaccess.__auth__).parameters(**kwargs)
    else:
        query = DataCollections().parameters(**kwargs)
    datasets_found = query.hits()
    logger.info(f"Datasets found: {datasets_found}")
    if count > 0:
        return query.get(count)
    return query.get_all()


def search_data(count: int = -1, **kwargs: Any) -> List[DataGranule]:
    """Search dataset granules using NASA's CMR.

    [https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)

    Parameters:
        count: Number of records to get, -1 = all
        kwargs (Dict):
            arguments to CMR:

            * **short_name**: dataset short name, e.g. ATL08
            * **version**: dataset version
            * **doi**: DOI for a dataset
            * **daac**: e.g. NSIDC or PODAAC
            * **provider**: particular to each DAAC, e.g. POCLOUD, LPDAAC etc.
            * **temporal**: a tuple representing temporal bounds in the form
              `(date_from, date_to)`
            * **bounding_box**: a tuple representing spatial bounds in the form
              `(lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)`

    Returns:
        a list of DataGranules that can be used to access the granule files by using
            `download()` or `open()`.

    Raises:
        RuntimeError: The CMR query failed.

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
    logger.info(f"Granules found: {granules_found}")
    if count > 0:
        return query.get(count)
    return query.get_all()


def search_services(count: int = -1, **kwargs: Any) -> List[Any]:
    """Search the NASA CMR for Services matching criteria.

    See <https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#service>.

    Parameters:
        count:
            maximum number of services to fetch (if less than 1, all services
            matching specified criteria are fetched [default])
        kwargs:
            keyword arguments accepted by the CMR for searching services

    Returns:
        list of services (possibly empty) matching specified criteria, in UMM
        JSON format

    Examples:
        ```python
        services = search_services(provider="POCLOUD", keyword="COG")
        ```
    """
    query = DataServices(auth=earthaccess.__auth__).parameters(**kwargs)
    hits = query.hits()
    logger.info(f"Services found: {hits}")

    return query.get(hits if count < 1 else min(count, hits))


def login(
    strategy: str = "all",
    persist: bool = False,
    system: System = PROD,
) -> Auth:
    """Authenticate with Earthdata login (https://urs.earthdata.nasa.gov/).

    Parameters:
        strategy:
            An authentication method.

            * **"all"**: (default) try all methods until one works
            * **"interactive"**: enter username and password.
            * **"netrc"**: retrieve username and password from ~/.netrc.
            * **"environment"**: retrieve either a username and password pair from
              the `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables,
              or an Earthdata login token from the `EARTHDATA_TOKEN` environment variable.
        persist: will persist credentials in a .netrc file
        system: the Earthdata system to access, defaults to PROD

    Returns:
        An instance of Auth.

    Raises:
        LoginAttemptFailure: If the NASA Earthdata Login service rejects
            credentials.
    """
    # Set the underlying Auth object's earthdata system,
    # before triggering the getattr function for `__auth__`.
    earthaccess._auth._set_earthdata_system(system)

    if strategy == "all":
        for strategy in ["environment", "netrc", "interactive"]:
            try:
                earthaccess.__auth__.login(
                    strategy=strategy,
                    persist=persist,
                    system=system,
                )
            except LoginStrategyUnavailable as err:
                logger.debug(err)
                continue

            if earthaccess.__auth__.authenticated:
                earthaccess.__store__ = Store(earthaccess.__auth__)
                break
    else:
        earthaccess.__auth__.login(
            strategy=strategy,
            persist=persist,
            system=system,
        )
        if earthaccess.__auth__.authenticated:
            earthaccess.__store__ = Store(earthaccess.__auth__)

    return earthaccess.__auth__


def download(
    granules: Union[DataGranule, List[DataGranule], str, List[str]],
    local_path: Optional[Union[Path, str]] = None,
    provider: Optional[str] = None,
    threads: int = 8,
    *,
    pqdm_kwargs: Optional[Mapping[str, Any]] = None,
) -> List[Path]:
    """Retrieves data granules from a remote storage system. Provide the optional `local_path` argument to prevent repeated downloads.

       * If we run this in the cloud, we will be using S3 to move data to `local_path`.
       * If we run it outside AWS (us-west-2 region) and the dataset is cloud hosted,
            we'll use HTTP links.

    Parameters:
        granules: a granule, list of granules, a granule link (HTTP), or a list of granule links (HTTP)
        local_path: Local directory to store the remote data granules.  If not
            supplied, defaults to a subdirectory of the current working directory
            of the form `data/YYYY-MM-DD-UUID`, where `YYYY-MM-DD` is the year,
            month, and day of the current date, and `UUID` is the last 6 digits
            of a UUID4 value.
        provider: if we download a list of URLs, we need to specify the provider.
        threads: parallel number of threads to use to download the files, adjust as necessary, default = 8
        pqdm_kwargs: Additional keyword arguments to pass to pqdm, a parallel processing library.
            See pqdm documentation for available options. Default is to use immediate exception behavior
            and the number of jobs specified by the `threads` parameter.

    Returns:
        List of downloaded files

    Raises:
        Exception: A file download failed.
    """
    provider = _normalize_location(str(provider))

    if isinstance(granules, DataGranule):
        granules = [granules]
    elif isinstance(granules, str):
        granules = [granules]

    try:
        return earthaccess.__store__.get(
            granules, local_path, provider, threads, pqdm_kwargs=pqdm_kwargs
        )
    except AttributeError as err:
        logger.error(
            f"{err}: You must call earthaccess.login() before you can download data"
        )

    return []


def open(
    granules: Union[List[str], List[DataGranule]],
    provider: Optional[str] = None,
    *,
    pqdm_kwargs: Optional[Mapping[str, Any]] = None,
) -> List[AbstractFileSystem]:
    """Returns a list of file-like objects that can be used to access files
    hosted on S3 or HTTPS by third party libraries like xarray.

    Parameters:
        granules: a list of granule instances **or** list of URLs, e.g. `s3://some-granule`.
            If a list of URLs is passed, we need to specify the data provider.
        provider: e.g. POCLOUD, NSIDC_CPRD, etc.
        pqdm_kwargs: Additional keyword arguments to pass to pqdm, a parallel processing library.
            See pqdm documentation for available options. Default is to use immediate exception behavior
            and the number of jobs specified by the `threads` parameter.

    Returns:
        A list of "file pointers" to remote (i.e. s3 or https) files.
    """
    return earthaccess.__store__.open(
        granules=granules,
        provider=_normalize_location(provider),
        pqdm_kwargs=pqdm_kwargs,
    )


def get_s3_credentials(
    daac: Optional[str] = None,
    provider: Optional[str] = None,
    results: Optional[List[DataGranule]] = None,
) -> Dict[str, Any]:
    """Returns temporary (1 hour) credentials for direct access to NASA S3 buckets. We can
    use the daac name, the provider, or a list of results from earthaccess.search_data().
    If we use results, earthaccess will use the metadata on the response to get the credentials,
    which is useful for missions that do not use the same endpoint as their DAACs, e.g. SWOT.

    Parameters:
        daac: a DAAC short_name like NSIDC or PODAAC, etc.
        provider: if we know the provider for the DAAC, e.g. POCLOUD, LPCLOUD etc.
        results: List of results from search_data()

    Returns:
        a dictionary with S3 credentials for the DAAC or provider
    """
    daac = _normalize_location(daac)
    provider = _normalize_location(provider)
    if results is not None:
        endpoint = results[0].get_s3_credentials_endpoint()
        return earthaccess.__auth__.get_s3_credentials(endpoint=endpoint)
    return earthaccess.__auth__.get_s3_credentials(daac=daac, provider=provider)


def collection_query() -> CollectionQuery:
    """Returns a query builder instance for NASA collections (datasets).

    Returns:
        a query builder instance for data collections.
    """
    if earthaccess.__auth__.authenticated:
        query_builder = DataCollections(earthaccess.__auth__)
    else:
        query_builder = DataCollections()
    return query_builder


def granule_query() -> GranuleQuery:
    """Returns a query builder instance for data granules.

    Returns:
        a query builder instance for data granules.
    """
    if earthaccess.__auth__.authenticated:
        query_builder = DataGranules(earthaccess.__auth__)
    else:
        query_builder = DataGranules()
    return query_builder


def get_fsspec_https_session() -> AbstractFileSystem:
    """Returns a fsspec session that can be used to access datafiles across many different DAACs.

    Returns:
        An fsspec instance able to access data across DAACs.

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
    """Returns a requests Session instance with an authorized bearer token.
    This is useful for making requests to restricted URLs, such as data granules or services that
    require authentication with NASA EDL.

    Returns:
        An authenticated requests Session instance.

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


@deprecated("Use get_s3_filesystem instead")
def get_s3fs_session(
    daac: Optional[str] = None,
    provider: Optional[str] = None,
    results: Optional[DataGranule] = None,
) -> s3fs.S3FileSystem:
    """Returns a fsspec s3fs file session for direct access when we are in us-west-2.

    Parameters:
        daac: Any DAAC short name e.g. NSIDC, GES_DISC
        provider: Each DAAC can have a cloud provider.
            If the DAAC is specified, there is no need to use provider.
        results: A list of results from search_data().
            `earthaccess` will use the metadata from CMR to obtain the S3 Endpoint.

    Returns:
        An `s3fs.S3FileSystem` authenticated for reading in-region in us-west-2 for 1 hour.
    """
    return get_s3_filesystem(daac, provider, results)


def get_s3_filesystem(
    daac: Optional[str] = None,
    provider: Optional[str] = None,
    results: Optional[DataGranule] = None,
    endpoint: Optional[str] = None,
) -> s3fs.S3FileSystem:
    """Return an `s3fs.S3FileSystem` for direct access when running within the AWS us-west-2 region.

    Parameters:
        daac: Any DAAC short name e.g. NSIDC, GES_DISC
        provider: Each DAAC can have a cloud provider.
            If the DAAC is specified, there is no need to use provider.
        results: A list of results from search_data().
            `earthaccess` will use the metadata from CMR to obtain the S3 Endpoint.
        endpoint: URL of a cloud provider credentials endpoint to be used for obtaining
            AWS S3 access credentials.

    Returns:
        An authenticated s3fs session valid for 1 hour.
    """
    daac = _normalize_location(daac)
    provider = _normalize_location(provider)
    if results:
        endpoint = results[0].get_s3_credentials_endpoint()
        if endpoint:
            session = earthaccess.__store__.get_s3_filesystem(endpoint=endpoint)
        else:
            raise ValueError("No s3 credentials specified in the given DataGranule")
    elif endpoint:
        session = earthaccess.__store__.get_s3_filesystem(endpoint=endpoint)
    elif daac or provider:
        session = earthaccess.__store__.get_s3_filesystem(daac=daac, provider=provider)
    else:
        raise ValueError(
            "Invalid set of input arguments given. Please provide either "
            "a valid result, an endpoint, a daac, or a provider."
        )
    return session


def get_edl_token() -> str:
    """Returns the current token used for EDL.

    Returns:
        EDL token
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
