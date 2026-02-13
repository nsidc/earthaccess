import datetime
import logging
import threading
import traceback
from functools import lru_cache
from itertools import chain
from pathlib import Path
from pickle import dumps, loads
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union
from uuid import uuid4

import fsspec
import requests
import s3fs
from multimethod import multimethod as singledispatchmethod
from pqdm.threads import pqdm
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from typing_extensions import deprecated

import earthaccess

from .auth import Auth
from .daac import DAAC_TEST_URLS, find_provider
from .exceptions import DownloadFailure, EulaNotAccepted
from .results import DataGranule
from .search import DataCollections

logger = logging.getLogger(__name__)


def _is_interactive() -> bool:
    """Detect if earthaccess is being used in an interactive session.
    Interactive sessions include Jupyter Notebooks, IPython REPL, and default Python REPL.
    """
    try:
        from IPython import get_ipython  # type: ignore

        # IPython Notebook or REPL:
        if get_ipython() is not None:
            return True
    except ImportError:
        pass

    import sys

    # Python REPL
    return hasattr(sys, "ps1")


class EarthAccessFile:
    """Handle for a file-like object pointing to an on-prem or Earthdata Cloud granule."""

    def __init__(
        self, f: fsspec.spec.AbstractBufferedFile, granule: DataGranule
    ) -> None:
        """EarthAccessFile connects an Earthdata search result with an open file-like object.

        The class implements custom serialization, but otherwise passes all attribute and method calls
        directly to the file-like object given during initialization. An instance of
        this class can be treated like that file-like object itself.

        Note that `type()` applied to an instance of this class is expected to disagree with
        the `__class__` attribute on the instance.

        Parameters:
            f: a file-like object
            granule: a granule search result
        """
        self.f = f
        self.granule = granule

    def __getattribute__(self, name: str) -> Any:
        # use super().__getattribute__ to avoid infinite recursion
        if (name in EarthAccessFile.__dict__) or (name in self.__dict__):
            # accessing our attributes
            return super().__getattribute__(name)
        else:
            # access proxied attributes
            proxy = super().__getattribute__("f")
            return getattr(proxy, name)

    def __reduce_ex__(self, protocol: Any) -> Any:
        return make_instance, (
            self.__class__,
            self.granule,
            earthaccess.__auth__,
            dumps(self.f),
        )

    def __repr__(self) -> str:
        return repr(self.f)


def _optimal_fsspec_block_size(file_size: int) -> int:
    """Determine the optimal block size based on file size.
    Note: we could even be smarter if we know the chunk sizes of the variables
    we need to cache, e.g. using the `dmrpp` file and the `wellknownparts` cache type.

    Uses `blockcache` for all files with block sizes adjusted by file size:

    - <100MB: 4MB
    - >100MB: 4–16MB

    Parameters:
        file_size (int): Size of the file in bytes.

    Returns:
        block_size (int): Optimal block size in bytes.
    """
    if file_size < 100 * 1024 * 1024:
        block_size = 4 * 1024 * 1024
    elif 100 * 1024 * 1024 <= file_size < 1024 * 1024 * 1024:
        block_size = 8 * 1024 * 1024
    else:
        block_size = 16 * 1024 * 1024

    return block_size


def _open_files(
    url_mapping: Mapping[str, Union[DataGranule, None]],
    fs: fsspec.AbstractFileSystem,
    *,
    pqdm_kwargs: Optional[Mapping[str, Any]] = None,
    open_kwargs: Optional[Dict[str, Any]] = None,
) -> List[fsspec.spec.AbstractBufferedFile]:
    def multi_thread_open(data: tuple[str, Optional[DataGranule]]) -> EarthAccessFile:
        url, granule = data
        f_size = fs.info(url)["size"]
        default_cache_type = "background"  # block cache with background fetching
        default_block_size = _optimal_fsspec_block_size(f_size)

        open_kw = (open_kwargs or fsspec.config.conf or {}).copy()

        open_kw.setdefault("cache_type", default_cache_type)
        open_kw.setdefault("block_size", default_block_size)

        f = fs.open(url, **open_kw)
        return EarthAccessFile(f, granule)  # type: ignore

    # this {#n_jobs} is for the unittests as this method is not public and pqdm will have values at this point
    return pqdm(
        url_mapping.items(), multi_thread_open, **(pqdm_kwargs or {"n_jobs": 8})
    )


def make_instance(
    cls: Any, granule: DataGranule, auth: Auth, data: Any
) -> EarthAccessFile:
    # Attempt to re-authenticate
    if not earthaccess.__auth__.authenticated:
        earthaccess.__auth__ = auth
        earthaccess.login()

    # When sending EarthAccessFiles between processes, it's possible that
    # we will need to switch between s3 <--> https protocols.
    if (earthaccess.__store__.in_region and cls is not s3fs.S3File) or (
        not earthaccess.__store__.in_region and cls is s3fs.S3File
    ):
        # NOTE: This uses the first data_link listed in the granule. That's not
        #       guaranteed to be the right one.
        return earthaccess.open([granule])[0]
    else:
        return EarthAccessFile(loads(data), granule)


def _get_url_granule_mapping(
    granules: List[DataGranule], access: str
) -> Mapping[str, DataGranule]:
    """Construct a mapping between file urls and granules."""
    url_mapping = {}
    for granule in granules:
        for url in granule.data_links(access=access):
            url_mapping[url] = granule
    return url_mapping


class Store(object):
    """Store class to access granules on-prem or in the cloud."""

    def __init__(self, auth: Any, pre_authorize: bool = False) -> None:
        """Store is the class to access data.

        Parameters:
            auth: Auth instance to download and access data.
        """
        self.thread_locals = threading.local()
        if auth.authenticated is True:
            self.auth = auth
            self._s3_credentials: Dict[
                Tuple, Tuple[datetime.datetime, Dict[str, str]]
            ] = {}
            oauth_profile = f"https://{auth.system.edl_hostname}/profile"
            # sets the initial URS cookie
            self._requests_cookies: Dict[str, Any] = {}
            self.set_requests_session(oauth_profile)
            if pre_authorize:
                # collect cookies from other DAACs
                for url in DAAC_TEST_URLS:
                    self.set_requests_session(url)

        else:
            logger.warning("The current session is not authenticated with NASA")
            self.auth = None
        self.in_region = self._running_in_us_west_2()

    def _derive_concept_provider(self, concept_id: Optional[str] = None) -> str:
        if concept_id is not None:
            provider = concept_id.split("-")[1]
            return provider
        return ""

    def _derive_daac_provider(self, daac: str) -> Union[str, None]:
        provider = find_provider(daac, True)
        return provider

    def _is_cloud_collection(self, concept_id: List[str]) -> bool:
        collection = DataCollections(self.auth).concept_id(concept_id).get()
        if len(collection) > 0 and "s3-links" in collection[0]["meta"]:
            return True
        return False

    def _own_s3_credentials(self, links: List[Dict[str, Any]]) -> Union[str, None]:
        for link in links:
            if "/s3credentials" in link["URL"]:
                return link["URL"]
        return None

    def _running_in_us_west_2(self) -> bool:
        session = self.auth.get_session()
        try:
            # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html
            token_ = session.put(
                "http://169.254.169.254/latest/api/token",
                headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
                timeout=1,
            )
            resp = session.get(
                "http://169.254.169.254/latest/meta-data/placement/region",
                timeout=1,
                headers={"X-aws-ec2-metadata-token": token_.text},
            )
        except Exception:
            return False

        if resp.status_code == 200 and b"us-west-2" == resp.content:
            # On AWS, in region us-west-2
            return True
        return False

    def set_requests_session(self, url: str, method: str = "get") -> None:
        """Sets up a `requests` session with bearer tokens that are used by CMR.

        Mainly used to get the authentication cookies from different DAACs and URS.
        This HTTPS session can be used to download granules if we want to use a direct,
        lower level API.

        Parameters:
            url: used to test the credentials and populate the class auth cookies
            method: HTTP method to test, default: "GET"
            bearer_token: if true, will be used for authenticated queries on CMR
        """
        if not hasattr(self, "_http_session"):
            self._http_session = self.auth.get_session()

        resp = self._http_session.request(method, url, allow_redirects=True)

        if resp.status_code in [400, 401, 403]:
            new_session = requests.Session()
            resp_req = new_session.request(
                method, url, allow_redirects=True, cookies=self._requests_cookies
            )
            if resp_req.status_code in [400, 401, 403]:
                resp.raise_for_status()
            else:
                self._requests_cookies.update(new_session.cookies.get_dict())
        elif 200 <= resp.status_code < 300:
            self._requests_cookies = self._http_session.cookies.get_dict()
        else:
            resp.raise_for_status()

    @deprecated("Use get_s3_filesystem instead")
    def get_s3fs_session(
        self,
        daac: Optional[str] = None,
        concept_id: Optional[str] = None,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> s3fs.S3FileSystem:
        """Returns a s3fs instance for a given cloud provider / DAAC.

        Parameters:
           daac: any of the DAACs, e.g. NSIDC, PODAAC
           provider: a data provider if we know them, e.g. PODAAC -> POCLOUD
           endpoint: pass the URL for the credentials directly

        Returns:
           An `s3fs.S3FileSystem` authenticated for reading in-region in us-west-2 for 1 hour.
        """
        return self.get_s3_filesystem(daac, concept_id, provider, endpoint)

    def get_s3_filesystem(
        self,
        daac: Optional[str] = None,
        concept_id: Optional[str] = None,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> s3fs.S3FileSystem:
        """Return an `s3fs.S3FileSystem` instance for a given cloud provider / DAAC.

        Parameters:
            daac: any of the DAACs, e.g. NSIDC, PODAAC
            provider: a data provider if we know them, e.g. PODAAC -> POCLOUD
            endpoint: pass the URL for the credentials directly

        Returns:
            a s3fs file instance
        """
        if self.auth is None:
            raise ValueError(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )
        if not any([concept_id, daac, provider, endpoint]):
            raise ValueError(
                "At least one of the concept_id, daac, provider or endpoint"
                "parameters must be specified. "
            )

        if concept_id is not None:
            provider = self._derive_concept_provider(concept_id)

        # Get existing S3 credentials if we already have them
        location = (
            daac,
            provider,
            endpoint,
        )  # Identifier for where to get S3 credentials from
        need_new_creds = False
        try:
            dt_init, creds = self._s3_credentials[location]
        except KeyError:
            need_new_creds = True
        else:
            # If cached credentials are expired, invalidate the cache
            delta = datetime.datetime.now() - dt_init
            if round(delta.seconds / 60, 2) > 55:
                need_new_creds = True
                self._s3_credentials.pop(location)

        if need_new_creds:
            # Don't have existing valid S3 credentials, so get new ones
            now = datetime.datetime.now()
            if endpoint is not None:
                creds = self.auth.get_s3_credentials(endpoint=endpoint)
            elif daac is not None:
                creds = self.auth.get_s3_credentials(daac=daac)
            elif provider is not None:
                creds = self.auth.get_s3_credentials(provider=provider)
            # Include new credentials in the cache
            self._s3_credentials[location] = now, creds

        return s3fs.S3FileSystem(
            key=creds["accessKeyId"],
            secret=creds["secretAccessKey"],
            token=creds["sessionToken"],
        )

    @lru_cache
    def get_fsspec_session(self) -> fsspec.AbstractFileSystem:
        """Returns a fsspec HTTPS session with bearer tokens that are used by CMR.

        This HTTPS session can be used to download granules if we want to use a direct,
        lower level API.

        Returns:
            fsspec HTTPFileSystem (aiohttp client session)
        """
        token = self.auth.token["access_token"]
        client_kwargs = {
            "headers": {"Authorization": f"Bearer {token}"},
            # This is important! If we trust the env and send a bearer token,
            # auth will fail!
            "trust_env": False,
        }
        session = fsspec.filesystem("https", client_kwargs=client_kwargs)
        return session

    def get_requests_session(self) -> requests.Session:
        """Returns a requests HTTPS session with bearer tokens that are used by CMR.

        This HTTPS session can be used to download granules if we want to use a direct,
        lower level API.

        Returns:
            requests Session
        """
        if hasattr(self, "_http_session"):
            return self._http_session
        else:
            raise AttributeError("The requests session hasn't been set up yet.")

    def open(
        self,
        granules: Union[List[str], List[DataGranule]],
        provider: Optional[str] = None,
        *,
        show_progress: Optional[bool] = None,
        credentials_endpoint: Optional[str] = None,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
        open_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[fsspec.spec.AbstractBufferedFile]:
        """Returns a list of file-like objects that can be used to access files
        hosted on S3 or HTTPS by third party libraries like xarray.

        Parameters:
            granules: a list of granule instances **or** list of URLs, e.g. `s3://some-granule`.
                If a list of URLs is passed, we need to specify the data provider.
            provider: e.g. POCLOUD, NSIDC_CPRD, etc.
            show_progress: whether or not to display a progress bar. If not specified, defaults to `True` for interactive sessions
                (i.e., in a notebook or a python REPL session), otherwise `False`.
            credentials_endpoint: S3 credentials endpoint
            pqdm_kwargs: Additional keyword arguments to pass to pqdm, a parallel processing library.
                See pqdm documentation for available options. Default is to use immediate exception behavior.
            open_kwargs: Additional keyword arguments to pass to `fsspec.open`, such as `cache_type` and `block_size`.
                Defaults to using `blockcache` with a block size determined by the file size (4 to 16MB).

        Returns:
            A list of "file pointers" to remote (i.e. `s3://` or `https://`) files.
        """
        if show_progress is None:
            show_progress = _is_interactive()

        pqdm_kwargs = {
            "exception_behaviour": "immediate",
            "n_jobs": 8,
            "disable": not show_progress,
            **(pqdm_kwargs or {}),
        }
        if len(granules):
            return self._open(
                granules,
                provider,
                credentials_endpoint=credentials_endpoint,
                pqdm_kwargs=pqdm_kwargs,
                open_kwargs=open_kwargs,
            )
        return []

    @singledispatchmethod
    def _open(
        self,
        granules: Union[List[str], List[DataGranule]],
        provider: Optional[str] = None,
        *,
        credentials_endpoint: Optional[str] = None,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
        open_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        raise NotImplementedError("granules should be a list of DataGranule or URLs")

    @_open.register
    def _open_granules(
        self,
        granules: List[DataGranule],
        provider: Optional[str] = None,
        *,
        credentials_endpoint: Optional[str] = None,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
        open_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        fileset: List = []
        total_size = round(sum([granule.size() for granule in granules]) / 1024, 2)
        logger.info(f"Opening {len(granules)} granules, approx size: {total_size} GB")

        if self.auth is None:
            raise ValueError(
                "A valid Earthdata login instance is required to retrieve credentials"
            )

        if self.in_region:
            if granules[0].cloud_hosted:
                access = "direct"
                provider = granules[0]["meta"]["provider-id"]
                endpoint = credentials_endpoint or self._own_s3_credentials(
                    granules[0]["umm"]["RelatedUrls"]
                )
                if endpoint is not None:
                    logger.info(f"using endpoint: {endpoint}")
                    s3_fs = self.get_s3_filesystem(endpoint=endpoint)
                else:
                    logger.info(f"using provider: {provider}")
                    s3_fs = self.get_s3_filesystem(provider=provider)
            else:
                access = "on_prem"
                s3_fs = None

            url_mapping = _get_url_granule_mapping(granules, access)
            if s3_fs is not None:
                try:
                    fileset = _open_files(
                        url_mapping,
                        fs=s3_fs,
                        pqdm_kwargs=pqdm_kwargs,
                        open_kwargs=open_kwargs,
                    )
                except Exception as e:
                    raise RuntimeError(
                        "An exception occurred while trying to access remote files on S3. "
                        "This may be caused by trying to access the data outside the us-west-2 region."
                        f"Exception: {traceback.format_exc()}"
                    ) from e
            else:
                fileset = self._open_urls_https(
                    url_mapping, pqdm_kwargs=pqdm_kwargs, open_kwargs=open_kwargs
                )
        else:
            url_mapping = _get_url_granule_mapping(granules, access="on_prem")
            fileset = self._open_urls_https(
                url_mapping, pqdm_kwargs=pqdm_kwargs, open_kwargs=open_kwargs
            )

        return fileset

    @_open.register
    def _open_urls(
        self,
        granules: List[str],
        provider: Optional[str] = None,
        *,
        credentials_endpoint: Optional[str] = None,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
        open_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        fileset: List = []
        s3_fs = None
        if isinstance(granules[0], str) and (
            granules[0].startswith("s3") or granules[0].startswith("http")
        ):
            # TODO: method to derive the DAAC from url?
            provider = provider
        else:
            raise ValueError(
                f"Schema for {granules[0]} is not recognized, must be an HTTP or S3 URL"
            )
        if self.auth is None:
            raise ValueError(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )

        url_mapping: Mapping[str, None] = {url: None for url in granules}
        if self.in_region and granules[0].startswith("s3"):
            if provider is not None:
                s3_fs = self.get_s3_filesystem(provider=provider)
            elif credentials_endpoint is not None:
                s3_fs = self.get_s3_filesystem(endpoint=credentials_endpoint)
            if s3_fs:
                try:
                    fileset = _open_files(
                        url_mapping,
                        fs=s3_fs,
                        pqdm_kwargs=pqdm_kwargs,
                        open_kwargs=open_kwargs,
                    )
                except Exception as e:
                    raise RuntimeError(
                        "An exception occurred while trying to access remote files on S3. "
                        "This may be caused by trying to access the data outside the us-west-2 region. "
                        f"Exception: {traceback.format_exc()}"
                    ) from e

                return fileset
            else:
                logger.error(
                    f"An error occurred while trying to retrieve the cloud credentials for provider: {provider}. endpoint: {credentials_endpoint}"
                )
                return fileset
        else:
            if granules[0].startswith("s3"):
                raise ValueError(
                    "We cannot open S3 links when we are not in-region, try using HTTPS links"
                )
            fileset = self._open_urls_https(url_mapping, pqdm_kwargs=pqdm_kwargs)
            return fileset

    def get(
        self,
        granules: Union[List[DataGranule], List[str]],
        local_path: Optional[Union[Path, str]] = None,
        provider: Optional[str] = None,
        threads: int = 8,
        *,
        credentials_endpoint: Optional[str] = None,
        show_progress: Optional[bool] = None,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> List[Path]:
        """Retrieves data granules from a remote storage system.

           * If we run this in the cloud,
             we are moving data from S3 to a cloud compute instance (EC2, AWS Lambda).
           * If we run it outside the us-west-2 region and the data granules are part of a cloud-based
             collection, the method will not get any files.
           * If we request data granules from an on-prem collection,
             the data will be effectively downloaded to a local directory.

        Parameters:
            granules: A list of granules(DataGranule) instances or a list of granule links (HTTP).
            local_path: Local directory to store the remote data granules.  If not
                supplied, defaults to a subdirectory of the current working directory
                of the form `data/YYYY-MM-DD-UUID`, where `YYYY-MM-DD` is the year,
                month, and day of the current date, and `UUID` is the last 6 digits
                of a UUID4 value.
            provider: a valid cloud provider, each DAAC has a provider code for their cloud distributions
            credentials_endpoint: If provided, this will be used to get S3 credentials
            threads: Parallel number of threads to use to download the files;
                adjust as necessary, default = 8.
            show_progress: whether or not to display a progress bar. If not specified, defaults to `True` for interactive sessions
                (i.e., in a notebook or a python REPL session), otherwise `False`.
            pqdm_kwargs: Additional keyword arguments to pass to pqdm, a parallel processing library.
                See pqdm documentation for available options. Default is to use immediate exception behavior
                and the number of jobs specified by the `threads` parameter.

        Returns:
            List of downloaded files
        """
        if not granules:
            raise ValueError("List of URLs or DataGranule instances expected")

        if local_path is None:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            uuid = uuid4().hex[:6]
            local_path = Path.cwd() / "data" / f"{today}-{uuid}"

        if show_progress is None:
            show_progress = _is_interactive()

        pqdm_kwargs = {
            "exception_behaviour": "immediate",  # should be overridden by pqdm_kwargs if passed
            "n_jobs": threads,
            "disable": not show_progress,
            **(pqdm_kwargs or {}),
        }

        return self._get(
            granules,
            Path(local_path),
            provider,
            credentials_endpoint=credentials_endpoint,
            pqdm_kwargs=pqdm_kwargs,
        )

    @singledispatchmethod
    def _get(
        self,
        granules: Union[List[DataGranule], List[str]],
        local_path: Path,
        provider: Optional[str] = None,
        *,
        credentials_endpoint: Optional[str] = None,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> List[Path]:
        """Retrieves data granules from a remote storage system.

           * If we run this in the cloud,
             we are moving data from S3 to a cloud compute instance (EC2, AWS Lambda).
           * If we run it outside the us-west-2 region and the data granules are part of a cloud-based
             collection, the method will not get any files.
           * If we request data granules from an on-prem collection,
             the data will be effectively downloaded to a local directory.

        Parameters:
            granules: A list of granules (DataGranule) instances or a list of granule links (HTTP).
            local_path: Local directory to store the remote data granules
            provider: a valid cloud provider, each DAAC has a provider code for their cloud distributions
            pqdm_kwargs: Additional keyword arguments to pass to pqdm, a parallel processing library.
                See pqdm documentation for available options. Default is to use immediate exception behavior
                and the number of jobs specified by the `threads` parameter.

        Returns:
            None
        """
        raise NotImplementedError(f"Cannot _get {granules}")

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def download_cloud_file(
        self, s3_fs: fsspec.AbstractFileSystem, file: str, local_path: Path
    ) -> Path:
        file_name = local_path / Path(file).name
        if file_name.exists():
            return file_name  # Skip if already exists

        s3_fs.get([file], str(local_path), recursive=False)
        logger.info(f"Downloading: {file_name}")
        return file_name

    @_get.register
    def _get_urls(
        self,
        granules: List[str],
        local_path: Path,
        provider: Optional[str] = None,
        *,
        credentials_endpoint: Optional[str] = None,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> List[Path]:
        data_links = granules
        s3_fs = s3fs.S3FileSystem()
        if (
            provider is None
            and credentials_endpoint is None
            and self.in_region
            and "cumulus" in data_links[0]
        ):
            raise ValueError(
                "earthaccess can't yet guess the provider for cloud collections, "
                "we need to use one from `earthaccess.list_cloud_providers()` or if known the S3 credential endpoint"
            )
        if self.in_region and data_links[0].startswith("s3"):
            if credentials_endpoint is not None:
                logger.info(
                    f"Accessing cloud dataset using credentials_endpoint: {credentials_endpoint}"
                )
                s3_fs = self.get_s3_filesystem(endpoint=credentials_endpoint)
            elif provider is not None:
                logger.info(f"Accessing cloud dataset using provider: {provider}")
                s3_fs = self.get_s3_filesystem(provider=provider)

            def _download(file: str) -> Union[Path, None]:
                return self.download_cloud_file(s3_fs, file, local_path)

            results = pqdm(data_links, _download, **pqdm_kwargs)
            return [r for r in results if r is not None]

        else:
            # if we are not in AWS
            return self._download_onprem_granules(
                data_links, local_path, pqdm_kwargs=pqdm_kwargs
            )

    @_get.register
    def _get_granules(
        self,
        granules: List[DataGranule],
        local_path: Path,
        provider: Optional[str] = None,
        *,
        credentials_endpoint: Optional[str] = None,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> List[Path]:
        data_links: List = []
        provider = granules[0]["meta"]["provider-id"]
        endpoint = self._own_s3_credentials(granules[0]["umm"]["RelatedUrls"])
        cloud_hosted = granules[0].cloud_hosted
        access = "direct" if (cloud_hosted and self.in_region) else "external"
        data_links = list(
            # we are not in-region
            chain.from_iterable(
                granule.data_links(access=access, in_region=self.in_region)
                for granule in granules
            )
        )
        total_size = round(sum(granule.size() for granule in granules) / 1024, 2)
        logger.info(
            f" Getting {len(granules)} granules, approx download size: {total_size} GB"
        )
        if access == "direct":
            if endpoint is not None:
                logger.info(
                    f"Accessing cloud dataset using dataset endpoint credentials: {endpoint}"
                )
                s3_fs = self.get_s3_filesystem(endpoint=endpoint)
            else:
                logger.info(f"Accessing cloud dataset using provider: {provider}")
                s3_fs = self.get_s3_filesystem(provider=provider)

            local_path.mkdir(parents=True, exist_ok=True)

            def _download(file: str) -> Union[Path, None]:
                return self.download_cloud_file(s3_fs, file, local_path)

            results = pqdm(data_links, _download, **pqdm_kwargs)
            return [r for r in results if r is not None]

        else:
            # if the data are cloud-based, but we are not in AWS,
            # it will be downloaded as if it was on prem
            return self._download_onprem_granules(
                data_links, local_path, pqdm_kwargs=pqdm_kwargs
            )

    def _clone_session_in_local_thread(
        self, original_session: requests.Session
    ) -> None:
        """Clone the original session and store it in the local thread context.

        This method creates a new session that replicates the headers, cookies, and authentication settings
        from the provided original session. The new session is stored in a thread-local storage.

        Parameters:
            original_session (SessionWithHeaderRedirection): The session to be cloned.

        Returns:
            None
        """
        if not hasattr(self.thread_locals, "local_thread_session"):
            local_thread_session = self.auth.get_session()  # type: ignore
            local_thread_session.headers.update(original_session.headers)
            local_thread_session.cookies.update(original_session.cookies)
            local_thread_session.auth = original_session.auth
            self.thread_locals.local_thread_session = local_thread_session

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _download_file(self, url: str, directory: Path) -> Path:
        """Download a single file using a bearer token.

        Parameters:
            url: the granule url
            directory: local directory

        Returns:
            A local filepath or an exception.
        """
        # If the get data link is an Opendap location
        if "opendap" in url and url.endswith(".html"):
            url = url.replace(".html", "")
        local_filename = url.split("/")[-1]
        path = directory / Path(local_filename)
        if not path.exists():
            original_session = self.get_requests_session()
            # This reuses the auth cookie, we make sure we only authenticate N threads instead
            # of one per file, see #913
            self._clone_session_in_local_thread(original_session)
            session = self.thread_locals.local_thread_session
            with session.get(url, stream=True, allow_redirects=True) as r:
                if r.status_code in [401, 403]:
                    text = (r.text or "").lower()
                    if "eula" in text:
                        raise EulaNotAccepted(f"Eula Acceptance Failure for {url}")
                if r.status_code >= 400:
                    raise DownloadFailure(
                        f"Download failed for {url}. Status code: {r.status_code}"
                    )

                with open(path, "wb") as f:
                    # Cap memory usage for large files at 1MB per write to disk per thread
                    # https://docs.python-requests.org/en/latest/user/quickstart/#raw-response-content
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)
        else:
            logger.info(f"File {local_filename} already downloaded")
        return path

    def _download_onprem_granules(
        self,
        urls: List[str],
        directory: Path,
        *,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> List[Any]:
        """Downloads a list of URLS into the data directory.

        Parameters:
            urls: list of granule URLs from an on-prem collection
            directory: local directory to store the downloaded files
            pqdm_kwargs: Additional keyword arguments to pass to pqdm, a parallel processing library.
                See pqdm documentation for available options. Default is to use immediate exception behavior
                and the number of jobs specified by the `threads` parameter.

        Returns:
            A list of local filepaths to which the files were downloaded.
        """
        if urls is None:
            raise ValueError("The granules didn't provide a valid GET DATA link")
        if self.auth is None:
            raise ValueError(
                "We need to be logged into NASA EDL in order to download data granules"
            )
        directory.mkdir(parents=True, exist_ok=True)

        arguments = [(url, directory) for url in urls]

        pqdm_kwargs = {
            "exception_behaviour": "immediate",
            "disable": True,
            **(pqdm_kwargs or {}),
            # We don't want a user to be able to override the following kwargs,
            # which is why they appear *after* spreading pqdm_kwargs above.
            "argument_type": "args",
        }

        return pqdm(arguments, self._download_file, **pqdm_kwargs)

    def _open_urls_https(
        self,
        url_mapping: Mapping[str, Union[DataGranule, None]],
        *,
        pqdm_kwargs: Optional[Mapping[str, Any]] = None,
        open_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[fsspec.AbstractFileSystem]:
        https_fs = self.get_fsspec_session()

        try:
            return _open_files(
                url_mapping, https_fs, pqdm_kwargs=pqdm_kwargs, open_kwargs=open_kwargs
            )
        except Exception:
            logger.exception(
                "An exception occurred while trying to access remote files via HTTPS"
            )
            raise
