import datetime
import os
import shutil
import traceback
from copy import deepcopy
from functools import lru_cache
from itertools import chain
from pathlib import Path
from pickle import dumps, loads
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import earthaccess
import fsspec
import requests
import s3fs
from multimethod import multimethod as singledispatchmethod
from pqdm.threads import pqdm

from .auth import Auth
from .daac import DAAC_TEST_URLS, find_provider
from .results import DataGranule
from .search import DataCollections


class EarthAccessFile(fsspec.spec.AbstractBufferedFile):
    def __init__(self, f: fsspec.AbstractFileSystem, granule: DataGranule) -> None:
        self.f = f
        self.granule = granule

    def __getattr__(self, method: str) -> Any:
        return getattr(self.f, method)

    def __reduce__(self) -> Any:
        return make_instance, (
            type(self.f),
            self.granule,
            earthaccess.__auth__,
            dumps(self.f),
        )

    def __repr__(self) -> str:
        return str(self.f)


def _open_files(
    data_links: List[str],
    granules: Union[List[str], List[DataGranule]],
    fs: fsspec.AbstractFileSystem,
    threads: Optional[int] = 8,
) -> List[fsspec.AbstractFileSystem]:
    def multi_thread_open(data: tuple) -> EarthAccessFile:
        urls, granule = data
        if type(granule) is not str:
            if len(granule.data_links()) > 1:
                print(
                    "Warning: This collection contains more than one file per granule. "
                    "earthaccess will only open the first data link, "
                    "try filtering the links before opening them."
                )
        return EarthAccessFile(fs.open(urls), granule)

    fileset = pqdm(zip(data_links, granules), multi_thread_open, n_jobs=threads)
    return fileset


def make_instance(
    cls: Any, granule: DataGranule, auth: Auth, data: Any
) -> EarthAccessFile:
    # Attempt to re-authenticate
    if not earthaccess.__auth__.authenticated:
        earthaccess.__auth__ = auth
        earthaccess.login()

    # When sending EarthAccessFiles between processes, it's possible that
    # we will need to switch between s3 <--> https protocols.
    if (earthaccess.__store__.running_in_aws and cls is not s3fs.S3File) or (
        not earthaccess.__store__.running_in_aws and cls is s3fs.S3File
    ):
        # NOTE: This uses the first data_link listed in the granule. That's not
        #       guaranteed to be the right one.
        return EarthAccessFile(earthaccess.open([granule])[0], granule)
    else:
        return EarthAccessFile(loads(data), granule)


class Store(object):
    """
    Store class to access granules on-prem or in the cloud.
    """

    def __init__(self, auth: Any, pre_authorize: bool = False) -> None:
        """Store is the class to access data

        Parameters:
            auth (Auth): Required, Auth instance to download and access data.
        """
        if auth.authenticated is True:
            self.auth = auth
            self.s3_fs = None
            self.initial_ts = datetime.datetime.now()
            oauth_profile = "https://urs.earthdata.nasa.gov/profile"
            # sets the initial URS cookie
            self._requests_cookies: Dict[str, Any] = {}
            self.set_requests_session(oauth_profile)
            if pre_authorize:
                # collect cookies from other daacs
                for url in DAAC_TEST_URLS:
                    self.set_requests_session(url)

        else:
            print("Warning: the current session is not authenticated with NASA")
            self.auth = None
        self.running_in_aws = self._am_i_in_aws()

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

    def _am_i_in_aws(self) -> bool:
        session = self.auth.get_session()
        try:
            # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html
            resp = session.get(
                "http://169.254.169.254/latest/meta-data/public-ipv4", timeout=1
            )
        except Exception:
            return False
        if resp.status_code == 200:
            return True
        return False

    def set_requests_session(
        self, url: str, method: str = "get", bearer_token: bool = False
    ) -> None:
        """Sets up a `requests` session with bearer tokens that are used by CMR.
        Mainly used to get the authentication cookies from different DAACs and URS
        This HTTPS session can be used to download granules if we want to use a direct, lower level API

        Parameters:
            url (String): used to test the credentials and populate the class auth cookies
            method (String): HTTP method to test. default: "GET"
            bearer_token (Boolean): if true will be used for authenticated queries on CMR

        Returns:
            fsspec HTTPFileSystem (aiohttp client session)
        """
        if not hasattr(self, "_http_session"):
            self._http_session = self.auth.get_session(bearer_token)

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
        elif resp.status_code >= 200 and resp.status_code <= 300:
            self._requests_cookies = self._http_session.cookies.get_dict()
        elif resp.status_code >= 500:
            resp.raise_for_status()

    @lru_cache
    def get_s3fs_session(
        self,
        daac: Optional[str] = None,
        concept_id: Optional[str] = None,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> s3fs.S3FileSystem:
        """
        Returns a s3fs instance for a given cloud provider / DAAC

        Parameters:
            daac: any of the DAACs e.g. NSIDC, PODAAC
            provider: a data provider if we know them, e.g PODAAC -> POCLOUD
            endpoint: pass the URL for the credentials directly
        Returns:
            a s3fs file instance
        """
        if self.auth is not None:
            if not any([concept_id, daac, provider, endpoint]):
                raise ValueError(
                    "At least one of the concept_id, daac, provider or endpoint"
                    "parameters must be specified. "
                )
            if endpoint is not None:
                s3_credentials = self.auth.get_s3_credentials(endpoint=endpoint)
            elif concept_id is not None:
                provider = self._derive_concept_provider(concept_id)
                s3_credentials = self.auth.get_s3_credentials(provider=provider)
            elif daac is not None:
                s3_credentials = self.auth.get_s3_credentials(daac=daac)
            elif provider is not None:
                s3_credentials = self.auth.get_s3_credentials(provider=provider)
            now = datetime.datetime.now()
            delta_minutes = now - self.initial_ts
            # TODO: test this mocking the time or use https://github.com/dbader/schedule
            # if we exceed 1 hour
            if (
                self.s3_fs is None or round(delta_minutes.seconds / 60, 2) > 59
            ) and s3_credentials is not None:
                self.s3_fs = s3fs.S3FileSystem(
                    key=s3_credentials["accessKeyId"],
                    secret=s3_credentials["secretAccessKey"],
                    token=s3_credentials["sessionToken"],
                )
                self.initial_ts = datetime.datetime.now()
            return deepcopy(self.s3_fs)
        else:
            raise ValueError(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )

    @lru_cache
    def get_fsspec_session(self) -> fsspec.AbstractFileSystem:
        """Returns a fsspec HTTPS session with bearer tokens that are used by CMR.
        This HTTPS session can be used to download granules if we want to use a direct, lower level API

        Returns:
            fsspec HTTPFileSystem (aiohttp client session)
        """
        token = self.auth.token["access_token"]
        client_kwargs = {
            "headers": {"Authorization": f"Bearer {token}"},
            # This is important! if we trust the env end send a bearer token
            # auth will fail!
            "trust_env": False,
        }
        session = fsspec.filesystem("https", client_kwargs=client_kwargs)
        return session

    def get_requests_session(self, bearer_token: bool = True) -> requests.Session:
        """Returns a requests HTTPS session with bearer tokens that are used by CMR.
        This HTTPS session can be used to download granules if we want to use a direct, lower level API

        Parameters:
            bearer_token (Boolean): if true will be used for authenticated queries on CMR

        Returns:
            requests Session
        """
        return self.auth.get_session()

    def open(
        self,
        granules: Union[List[str], List[DataGranule]],
        provider: Optional[str] = None,
    ) -> List[Any]:
        """Returns a list of fsspec file-like objects that can be used to access files
        hosted on S3 or HTTPS by third party libraries like xarray.

        Parameters:
            granules (List): a list of granules(DataGranule) instances or list of URLs, e.g. s3://some-granule
        Returns:
            a list of s3fs "file pointers" to s3 files.
        """
        if len(granules):
            return self._open(granules, provider)
        return []

    @singledispatchmethod
    def _open(
        self,
        granules: Union[List[str], List[DataGranule]],
        provider: Optional[str] = None,
    ) -> List[Any]:
        """Returns a list of fsspec file-like objects that can be used to access files
        hosted on S3 or HTTPS by third party libraries like xarray.

        Parameters:
            granules (List): a list of granules(DataGranule) instances or list of URLs, e.g. s3://some-granule
        Returns:
            a list of s3fs "file pointers" to s3 files.
        """
        raise NotImplementedError("granules should be a list of DataGranule or URLs")

    @_open.register
    def _open_granules(
        self,
        granules: List[DataGranule],
        provider: Optional[str] = None,
        threads: Optional[int] = 8,
    ) -> List[Any]:
        fileset: List = []
        data_links: List = []
        total_size = round(sum([granule.size() for granule in granules]) / 1024, 2)
        print(f"Opening {len(granules)} granules, approx size: {total_size} GB")

        if self.auth is None:
            raise ValueError(
                "A valid Earthdata login instance is required to retrieve credentials"
            )

        if self.running_in_aws:
            if granules[0].cloud_hosted:
                access_method = "direct"
                provider = granules[0]["meta"]["provider-id"]
                # if the data has its own S3 credentials endpoint we'll use it
                endpoint = self._own_s3_credentials(granules[0]["umm"]["RelatedUrls"])
                if endpoint is not None:
                    print(f"using endpoint: {endpoint}")
                    s3_fs = self.get_s3fs_session(endpoint=endpoint)
                else:
                    print(f"using provider: {provider}")
                    s3_fs = self.get_s3fs_session(provider=provider)
            else:
                access_method = "on_prem"
                s3_fs = None

            data_links = list(
                chain.from_iterable(
                    granule.data_links(access=access_method) for granule in granules
                )
            )

            if s3_fs is not None:
                try:
                    fileset = _open_files(
                        data_links=data_links,
                        granules=granules,
                        fs=s3_fs,
                        threads=threads,
                    )
                except Exception as e:
                    raise RuntimeError(
                        "An exception occurred while trying to access remote files on S3. "
                        "This may be caused by trying to access the data outside the us-west-2 region."
                        f"Exception: {traceback.format_exc()}"
                    ) from e
            else:
                fileset = self._open_urls_https(data_links, granules, threads=threads)
            return fileset
        else:
            access_method = "on_prem"
            data_links = list(
                chain.from_iterable(
                    granule.data_links(access=access_method) for granule in granules
                )
            )
            fileset = self._open_urls_https(data_links, granules, threads=threads)
            return fileset

    @_open.register
    def _open_urls(
        self,
        granules: List[str],
        provider: Optional[str] = None,
        threads: Optional[int] = 8,
    ) -> List[Any]:
        fileset: List = []
        data_links: List = []

        if isinstance(granules[0], str) and (
            granules[0].startswith("s3") or granules[0].startswith("http")
        ):
            # TODO: method to derive the DAAC from url?
            provider = provider
            data_links = granules
        else:
            raise ValueError(
                f"Schema for {granules[0]} is not recognized, must be an HTTP or S3 URL"
            )
        if self.auth is None:
            raise ValueError(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )

        if self.running_in_aws and granules[0].startswith("s3"):
            if provider is not None:
                s3_fs = self.get_s3fs_session(provider=provider)
                if s3_fs is not None:
                    try:
                        fileset = _open_files(
                            data_links=data_links,
                            granules=granules,
                            fs=s3_fs,
                            threads=threads,
                        )
                    except Exception as e:
                        raise RuntimeError(
                            "An exception occurred while trying to access remote files on S3. "
                            "This may be caused by trying to access the data outside the us-west-2 region."
                            f"Exception: {traceback.format_exc()}"
                        ) from e
                else:
                    print(f"Provider {provider} has no valid cloud credentials")
                return fileset
            else:
                raise ValueError(
                    "earthaccess cannot derive the DAAC provider from URLs only, a provider is needed e.g. POCLOUD"
                )
        else:
            if granules[0].startswith("s3"):
                raise ValueError(
                    "We cannot open S3 links when we are not in-region, try using HTTPS links"
                )
            fileset = self._open_urls_https(data_links, granules, threads)
            return fileset

    def get(
        self,
        granules: Union[List[DataGranule], List[str]],
        local_path: Optional[str] = None,
        provider: Optional[str] = None,
        threads: int = 8,
    ) -> List[str]:
        """Retrieves data granules from a remote storage system.

           * If we run this in the cloud we are moving data from S3 to a cloud compute instance (EC2, AWS Lambda)
           * If we run it outside the us-west-2 region and the data granules are part of a cloud-based
             collection the method will not get any files.
           * If we requests data granules from an on-prem collection the data will be effectively downloaded
             to a local directory.

        Parameters:
            granules: a list of granules(DataGranule) instances or a list of granule links (HTTP)
            local_path: local directory to store the remote data granules
            access: direct or on_prem, if set it will use it for the access method.
            threads: parallel number of threads to use to download the files, adjust as necessary, default = 8

        Returns:
            List of downloaded files
        """
        if local_path is None:
            local_path = os.path.join(
                ".",
                "data",
                f"{datetime.datetime.today().strftime('%Y-%m-%d')}-{uuid4().hex[:6]}",
            )
        if len(granules):
            files = self._get(granules, local_path, provider, threads)
            return files
        else:
            raise ValueError("List of URLs or DataGranule isntances expected")

    @singledispatchmethod
    def _get(
        self,
        granules: Union[List[DataGranule], List[str]],
        local_path: str,
        provider: Optional[str] = None,
        threads: int = 8,
    ) -> List[str]:
        """Retrieves data granules from a remote storage system.

           * If we run this in the cloud we are moving data from S3 to a cloud compute instance (EC2, AWS Lambda)
           * If we run it outside the us-west-2 region and the data granules are part of a cloud-based
             collection the method will not get any files.
           * If we requests data granules from an on-prem collection the data will be effectively downloaded
             to a local directory.

        Parameters:
            granules: a list of granules(DataGranule) instances or a list of granule links (HTTP)
            local_path: local directory to store the remote data granules
            access: direct or on_prem, if set it will use it for the access method.
            threads: parallel number of threads to use to download the files, adjust as necessary, default = 8

        Returns:
            None
        """
        raise NotImplementedError(f"Cannot _get {granules}")

    @_get.register
    def _get_urls(
        self,
        granules: List[str],
        local_path: str,
        provider: Optional[str] = None,
        threads: int = 8,
    ) -> List[str]:
        data_links = granules
        downloaded_files: List = []
        if provider is None and self.running_in_aws and "cumulus" in data_links[0]:
            raise ValueError(
                "earthaccess can't yet guess the provider for cloud collections, "
                "we need to use one from earthaccess.list_cloud_providers()"
            )
        if self.running_in_aws and data_links[0].startswith("s3"):
            print(f"Accessing cloud dataset using provider: {provider}")
            s3_fs = self.get_s3fs_session(provider=provider)
            # TODO: make this parallel or concurrent
            for file in data_links:
                s3_fs.get(file, local_path)
                file_name = os.path.join(local_path, os.path.basename(file))
                print(f"Downloaded: {file_name}")
                downloaded_files.append(file_name)
            return downloaded_files

        else:
            # if we are not in AWS
            return self._download_onprem_granules(data_links, local_path, threads)

    @_get.register
    def _get_granules(
        self,
        granules: List[DataGranule],
        local_path: str,
        provider: Optional[str] = None,
        threads: int = 8,
    ) -> List[str]:
        data_links: List = []
        downloaded_files: List = []
        provider = granules[0]["meta"]["provider-id"]
        endpoint = self._own_s3_credentials(granules[0]["umm"]["RelatedUrls"])
        cloud_hosted = granules[0].cloud_hosted
        access = "direct" if (cloud_hosted and self.running_in_aws) else "external"
        data_links = list(
            # we are not in region
            chain.from_iterable(
                granule.data_links(access=access, in_region=self.running_in_aws)
                for granule in granules
            )
        )
        total_size = round(sum([granule.size() for granule in granules]) / 1024, 2)
        print(
            f" Getting {len(granules)} granules, approx download size: {total_size} GB"
        )
        if access == "direct":
            if endpoint is not None:
                print(
                    f"Accessing cloud dataset using dataset endpoint credentials: {endpoint}"
                )
                s3_fs = self.get_s3fs_session(endpoint=endpoint)
            else:
                print(f"Accessing cloud dataset using provider: {provider}")
                s3_fs = self.get_s3fs_session(provider=provider)
            # TODO: make this async
            for file in data_links:
                s3_fs.get(file, local_path)
                file_name = os.path.join(local_path, os.path.basename(file))
                print(f"Downloaded: {file_name}")
                downloaded_files.append(file_name)
            return downloaded_files
        else:
            # if the data is cloud based bu we are not in AWS it will be downloaded as if it was on prem
            return self._download_onprem_granules(data_links, local_path, threads)

    def _download_file(self, url: str, directory: str) -> str:
        """
        download a single file from an on-prem location, a DAAC data center.
        :param url: the granule url
        :param directory: local directory
        :returns: local filepath or an exception
        """
        # If the get data link is an Opendap location
        if "opendap" in url and url.endswith(".html"):
            url = url.replace(".html", "")
        local_filename = url.split("/")[-1]
        path = Path(directory) / Path(local_filename)
        local_path = str(path)
        if not os.path.exists(local_path):
            try:
                session = self.auth.get_session()
                with session.get(
                    url,
                    stream=True,
                    allow_redirects=True,
                ) as r:
                    r.raise_for_status()
                    with open(local_path, "wb") as f:
                        # This is to cap memory usage for large files at 1MB per write to disk per thread
                        # https://docs.python-requests.org/en/master/user/quickstart/#raw-response-content
                        shutil.copyfileobj(r.raw, f, length=1024 * 1024)
            except Exception:
                print(f"Error while downloading the file {local_filename}")
                print(traceback.format_exc())
                raise Exception
        else:
            print(f"File {local_filename} already downloaded")
        return local_path

    def _download_onprem_granules(
        self, urls: List[str], directory: str, threads: int = 8
    ) -> List[Any]:
        """
        downloads a list of URLS into the data directory.
        :param urls: list of granule URLs from an on-prem collection
        :param directory: local directory to store the files
        :param threads: parallel number of threads to use to download the files, adjust as necessary, default = 8
        :returns: None
        """
        if urls is None:
            raise ValueError("The granules didn't provide a valid GET DATA link")
        if self.auth is None:
            raise ValueError(
                "We need to be logged into NASA EDL in order to download data granules"
            )
        if not os.path.exists(directory):
            os.makedirs(directory)

        arguments = [(url, directory) for url in urls]
        results = pqdm(
            arguments,
            self._download_file,
            n_jobs=threads,
            argument_type="args",
        )
        return results

    def _open_urls_https(
        self,
        urls: List[str],
        granules: Union[List[str], List[DataGranule]],
        threads: Optional[int] = 8,
    ) -> List[fsspec.AbstractFileSystem]:
        https_fs = self.get_fsspec_session()
        if https_fs is not None:
            try:
                fileset = _open_files(urls, granules, https_fs, threads)
            except Exception:
                print(
                    "An exception occurred while trying to access remote files via HTTPS: "
                    f"Exception: {traceback.format_exc()}"
                )
        return fileset
