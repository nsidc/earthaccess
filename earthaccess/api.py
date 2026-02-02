import json
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
from earthaccess.exceptions import LoginStrategyUnavailable, ServiceOutage
from earthaccess.services import DataServices

from .auth import Auth
from .results import DataCollection, DataGranule
from .search import CollectionQuery, DataCollections, DataGranules, GranuleQuery
from .store import Store
from .system import PROD, System
from .utils import _validation as validate

logger = logging.getLogger(__name__)


def status(system: System = PROD, raise_on_outage: bool = False) -> dict[str, str]:
    """Get the statuses of NASA's Earthdata services.

    Parameters:
        system: The Earthdata system to access, defaults to PROD.
        raise_on_outage: If True, raises exception on errors or outages.

    Returns:
        A dictionary containing the statuses of Earthdata services.

    Examples:
        >>> earthaccess.status()  # doctest: +SKIP
        {'Earthdata Login': 'OK', 'Common Metadata Repository': 'OK'}
        >>> earthaccess.status(earthaccess.UAT)  # doctest: +SKIP
        {'Earthdata Login': 'OK', 'Common Metadata Repository': 'OK'}

    Raises:
        ServiceOutage: if at least one service status is not `"OK"`
    """
    services = ("Earthdata Login", "Common Metadata Repository")
    statuses = {service: "Unknown" for service in services}
    msg = (
        f"Unable to retrieve Earthdata service statuses for {system}."
        f"  Try again later, or visit {system.status_url} to check service statuses."
    )

    try:
        with requests.get(system.status_api_url) as r:
            r.raise_for_status()
            statuses_json = r.json()

        for entry in statuses_json.get("statuses", []):
            name = entry.get("name", "")

            if service := next(filter(name.startswith, services), None):
                statuses[service] = entry.get("status", "Unknown")
    except (json.JSONDecodeError, requests.exceptions.RequestException):
        logger.error(msg)

    if raise_on_outage and any(
        status not in {"OK", "Unknown"} for status in statuses.values()
    ):
        msg = f"At least 1 service is in an unhealthy/unknown state: {services}"
        raise ServiceOutage(msg)

    return statuses


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
    """Search datasets (collections) using NASA's CMR.

    [https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)

    Parameters:
        count: Number of records to get, -1 = all
        kwargs (Dict):
            arguments to CMR:

            * **keyword**: (str) Filter collections by keywords.  Case-insensitive and
              supports wildcards ? and *
            * **short_name**: (str) Filter collections by product short name; e.g. ATL08
            * **doi**: (str) Filter by DOI
            * **daac**: (str) Filter by DAAC; e.g. NSIDC or PODAAC
            * **data_center**: (str) An alias for `daac`
            * **provider**: (str) Filter by data provider; each DAAC can have more than
               one provider, e.g. POCLOUD, PODAAC, etc.
            * **has_granules**: (bool) If true, only return collections with granules.  Default: True
            * **temporal**: (tuple) A tuple representing temporal bounds in the form
              `(date_from, date_to)`.  Dates can be `datetime` objects or ISO 8601
              formatted strings.  Date strings can be full timestamps; e.g. YYYY-MM-DD HH:mm:ss
              or truncated YYYY-MM-DD
            * **bounding_box**: (tuple) Filter collection by those that intersect bounding box.
              A tuple representing spatial bounds in the form
              `(lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)`
            * **polygon**: (List[tuples]) Filter by polygon.  Polygon must be a list of
              tuples containing longitude-latitude pairs representing polygon vertices.
              Vertices must be in counter-clockwise order and the final vertex must be the
              same as the first vertex; e.g. [(lon1,lat1),(lon2,lat2),(lon3,lat3),(lon4,lat4),(lon1,lat1)]
            * **point**: (Tuple[float,float])  Filter by collections intersecting a point,
              where the point is a longitude-latitude pair; e.g. (lon,lat)
            * **line**: (List[tuples]) Filter collections that overlap a series of connected
              points.  Points are represented as tuples containing longitude-latitude pairs;
              e.g. [(lon1,lat1),(lon2,lat2),(lon3,lat3)]
            * **circle**: (List[float, float, float]) Filter collections that intersect a
              circle defined as a point with a radius.  Circle parameters are a list
              containing latitude, longitude and radius in meters; e.g. [lon, lat, radius_m].
              The circle center cannot be the north or south poles.  The radius mst be
              between 10 and 6,000,000 m
            * **cloud_hosted**: (bool) Return only collected hosted on Earthdata Cloud.  Default: True
            * **downloadable**: (bool) If True, only return collections that can be downloaded
              from an online archive
            * **concept_id**: (str) Filter by Concept ID; e.g. C3151645377-NSIDC_CPRD
            * **instrument**: (str) Filter by Instrument name; e.g. ATLAS
            * **project**: (str) Filter by project or campaign name; e.g. ABOVE
            * **fields**: (List[str]) Return only the UMM fields listed in this parameter
            * **revision_date**: tuple(str,str) Filter by collections that have revision date
              within the range
            * **debug**: (bool) If True prints CMR request.  Default: True

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

        ```python
        results = earthaccess.search_datasets(
            daac="NSIDC",
            bounding_box=(-73., 58., -10., 84.),
        )
        ```

        ```python
        results = earthaccess.search_datasets(
            instrument="ATLAS",
            bounding_box=(-73., 58., -10., 84.),
            temporal=("2024-09-01", "2025-04-30"),
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
    """Search for dataset files (granules) using NASA's CMR.

    [https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)

    The CMR does not permit queries across all granules in all collections in order to provide fast search responses. Granule queries must target a subset of the collections in the CMR using a condition like provider, provider_id, concept_id, collection_concept_id, short_name, version or entry_title.

    Parameters:
        count: Number of records to get, -1 = all
        kwargs (Dict):
            arguments to CMR:

            * **short_name**: (str) Filter granules by product short name; e.g. ATL08
            * **version**: (str) Filter by dataset version
            * **daac**: (str) a provider code for any DAAC, e.g. NSIDC or PODAAC
            * **data_center**; (str) An alias for daac
            * **provider**: (str) Only match granules from a given provider.  A DAAC can
              have more than one provider, e.g PODAAC and POCLOUD, NSIDC_ECS and NSIDC_CPRD.
            * **cloud_hosted**: (bool) If True, only match granules hosted in Earthdata Cloud
            * **downloadable**: (bool) If True, only match granules that are downloadable.
              A granule is downloadable when it contains at least one RelatedURL of type
              GETDATA.
            * **online_only**: (bool) Alias of downloadable
            * **orbit_number**; (float) Filter granule by the orbit number in which a
              granule was acquired
            * **granule_name**; (str) Filter by granule name.  Granule name can contain
              wild cards, e.g `MODGRNLD.*.daily.*`.
            * **instrument**; (str) Filter by instrument name, e.g. "ATLAS"
            * **platform**; (str) Filter by platform, e.g. satellite or plane
            * **cloud_cover**: (tuple) Filter by cloud cover.  Tuple is a range of
              cloud covers, e.g. (0, 20).  Cloud cover values in metadata may be fractions
              (i.e. (0.,0.2)) or percentages.  CMRS searches for cloud cover range based on
              values in metadata. Note collections without cloud_cover in metadata will return
              zero granules.
            * **day_night_flag**: (str) Filter for day- and night-time images, accepts
              'day', 'night', 'unspecified'.
            * **temporal**: (tuple) A tuple representing temporal bounds in the form
              `(date_from, date_to)`.  Dates can be `datetime` objects or ISO 8601
              formatted strings.  Date strings can be full timestamps; e.g. YYYY-MM-DD HH:mm:ss
              or truncated YYYY-MM-DD
            * **bounding_box**: (tuple) Filter collection by those that intersect bounding box.
              A tuple representing spatial bounds in the form
              `(lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)`
            * **polygon**: (list[tuples]) Filter by polygon.  Polygon must be a list of
              tuples containing longitude-latitude pairs representing polygon vertices.
              Vertices must be in counter-clockwise order and the final vertex must be the
              same as the first vertex; e.g. [(lon1,lat1),(lon2,lat2),(lon3,lat3),
              (lon4,lat4),(lon1,lat1)]
            * **point**: (tuple(float,float))  Filter by collections intersecting a point,
              where the point is a longitude-latitude pair; e.g. (lon,lat)
            * **line**: (list[tuples]) Filter collections that overlap a series of connected
              points.  Points are represented as tuples containing longitude-latitude pairs;
              e.g. [(lon1,lat1),(lon2,lat2),(lon3,lat3)]
            * **circle**: (tuple(float, float, float)) Filter collections that intersect a
              circle defined as a point with a radius.  Circle parameters are a tuple
              containing latitude, longitude and radius in meters; e.g. (lon, lat, radius_m).
              The circle center cannot be the north or south poles.  The radius mst be
              between 10 and 6,000,000 m


    Returns:
        a list of DataGranules that can be used to access the granule files by using
            `download()` or `open()`.

    Raises:
        RuntimeError: The CMR query failed.

    Examples:
        ```python
        granules = earthaccess.search_data(
            short_name="ATL06",
            bounding_box=(-46.5, 61.0, -42.5, 63.0),
            )
        ```

        ```python
        granules = earthaccess.search_data(
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

    Attempt to login via _only_ the specified strategy, unless the `"all"`
    strategy is used, in which case each of the individual strategies is
    attempted in the following order, until one succeeds: `"environment"`,
    `"netrc"`, `"interactive"`.  In this case, only when all strategies fail
    does login fail.

    Parameters:
        strategy:
            An authentication method.

            * `"all"`: try each of the following methods, in order, until one
              succeeds.
            * `"environment"`: retrieve either an Earthdata login token from the
              `EARTHDATA_TOKEN` environment variable, or a username and password
              pair from the `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`
              environment variables (specifying a token takes precedence).
            * `"netrc"`: retrieve username and password from `~/.netrc` (or
              `~/_netrc` on Windows), or from the file specified by the `NETRC`
              environment variable.
            * `"interactive"`: enter username and password via interactive
              prompts.
        persist: if `True`, persist credentials to a `.netrc` file
        system: the Earthdata system to access

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
    show_progress: Optional[bool] = None,
    credentials_endpoint: Optional[str] = None,
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
        credentials_endpoint: S3 credentials endpoint to be used for obtaining temporary S3 credentials. This is only required if
            the metadata doesn't include it, or we pass urls to the method instead of `DataGranule` instances.
        threads: parallel number of threads to use to download the files, adjust as necessary, default = 8
        show_progress: whether or not to display a progress bar. If not specified, defaults to `True` for interactive sessions
            (i.e., in a notebook or a python REPL session), otherwise `False`.
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
            granules,
            local_path,
            provider,
            threads,
            credentials_endpoint=credentials_endpoint,
            show_progress=show_progress,
            pqdm_kwargs=pqdm_kwargs,
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
    credentials_endpoint: Optional[str] = None,
    show_progress: Optional[bool] = None,
    pqdm_kwargs: Optional[Mapping[str, Any]] = None,
    open_kwargs: Optional[Dict[str, Any]] = None,
) -> List[AbstractFileSystem]:
    """Returns a list of file-like objects that can be used to access files
    hosted on S3 or HTTPS by third party libraries like xarray.

    Parameters:
        granules: a list of granule instances **or** list of URLs, e.g. `s3://some-granule`.
            If a list of URLs is passed, we need to specify the data provider.
        provider: e.g. POCLOUD, NSIDC_CPRD, etc.
        show_progress: whether or not to display a progress bar. If not specified, defaults to `True` for interactive sessions
            (i.e., in a notebook or a python REPL session), otherwise `False`.
        pqdm_kwargs: Additional keyword arguments to pass to pqdm, a parallel processing library.
            See pqdm documentation for available options. Default is to use immediate exception behavior
            and the number of jobs specified by the `threads` parameter.
        open_kwargs: Additional keyword arguments to pass to `fsspec.open`, such as `cache_type` and `block_size`.
            Defaults to using `blockcache` with a block size determined by the file size (4 to 16MB).

    Returns:
        A list of "file pointers" to remote (i.e. s3 or https) files.
    """
    return earthaccess.__store__.open(
        granules=granules,
        provider=_normalize_location(provider),
        credentials_endpoint=credentials_endpoint,
        show_progress=show_progress,
        pqdm_kwargs=pqdm_kwargs,
        open_kwargs=open_kwargs,
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
