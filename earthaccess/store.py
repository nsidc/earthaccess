import datetime
import os
import shutil
import traceback
from copy import deepcopy
from itertools import chain
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import aiohttp
import fsspec
import requests
import s3fs
from multimethod import multimethod as singledispatchmethod
from pqdm.threads import pqdm

from .auth import SessionWithHeaderRedirection
from .daac import DAAC_TEST_URLS, find_provider
from .results import DataGranule
from .search import DataCollections


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
            self.set_requests_session(oauth_profile)
            self._requests_cookies: Dict[str, Any] = {}
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

    def get_s3fs_session(
        self,
        daac: Optional[str] = None,
        concept_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> s3fs.S3FileSystem:
        """
        Returns a s3fs instance for a given cloud provider / DAAC

        Parameters:
            daac: any of the DAACs e.g. NSIDC, PODAAC
        Returns:
            a s3fs file instance
        """
        if self.auth is not None:
            if concept_id is not None:
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
            print(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )
            return None

    def get_fsspec_session(self) -> fsspec.AbstractFileSystem:
        """Returns a fsspec HTTPS session with bearer tokens that are used by CMR.
        This HTTPS session can be used to download granules if we want to use a direct, lower level API

        Returns:
            fsspec HTTPFileSystem (aiohttp client session)
        """
        client_kwargs = {
            "auth": aiohttp.BasicAuth(
                self.auth._credentials[0], self.auth._credentials[1]
            ),
            "trust_env": True,
            "cookies": self._requests_cookies,
        }
        session = fsspec.filesystem("https", client_kwargs=client_kwargs)
        return session

    def get_requests_session(
        self, bearer_token: bool = False
    ) -> SessionWithHeaderRedirection:
        """Returns a requests HTTPS session with bearer tokens that are used by CMR.
        This HTTPS session can be used to download granules if we want to use a direct, lower level API

        Parameters:
            bearer_token (Boolean): if true will be used for authenticated queries on CMR

        Returns:
            requests Session
        """
        if not hasattr(self, "_http_session"):
            self._http_session = self.auth.get_session()
        return deepcopy(self._http_session)

    def open(
        self,
        granules: Union[List[str], List[DataGranule]],
        provider: Optional[str] = None,
    ) -> Union[List[Any], None]:
        """Returns a list of fsspec file-like objects that can be used to access files
        hosted on S3 or HTTPS by third party libraries like xarray.

        Parameters:
            granules (List): a list of granules(DataGranule) instances or list of URLs, e.g. s3://some-granule
        Returns:
            a list of s3fs "file pointers" to s3 files.
        """
        if len(granules):
            return self._open(granules, provider)
        print("The granules list is empty, moving on...")
        return None

    @singledispatchmethod
    def _open(
        self,
        granules: Union[List[str], List[DataGranule]],
        provider: Optional[str] = None,
    ) -> Union[List[Any], None]:
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
    ) -> Union[List[Any], None]:

        fileset: List = []
        data_links: List = []
        if self.running_in_aws:
            access_method = "direct"
        else:
            # on prem is a little misleading, for cloud collections this means external access.
            access_method = "on_prem"

        provider = granules[0]["meta"]["provider-id"]
        data_links = list(
            chain.from_iterable(
                granule.data_links(access=access_method) for granule in granules
            )
        )
        total_size = round(sum([granule.size() for granule in granules]) / 1024, 2)
        print(f" Opening {len(granules)} granules, approx size: {total_size} GB")

        if self.auth is None:
            print(
                "A valid Earthdata login instance is required to retrieve credentials"
            )
            return None

        if self.running_in_aws:
            s3_fs = self.get_s3fs_session(provider=provider)
            if s3_fs is not None:
                try:

                    def multi_thread_open(url: str) -> Any:
                        return s3_fs.open(url)

                    fileset = pqdm(data_links, multi_thread_open, n_jobs=8)

                except Exception:
                    print(
                        "An exception occurred while trying to access remote files on S3: "
                        "This may be caused by trying to access the data outside the us-west-2 region"
                        f"Exception: {traceback.format_exc()}"
                    )
                    return None
            return fileset
        else:
            https_fs = self.get_fsspec_session()
            if https_fs is not None:
                try:

                    def multi_thread_open(url: str) -> Any:
                        return https_fs.open(url)

                    fileset = pqdm(data_links, multi_thread_open, n_jobs=8)

                    # fileset = [https_fs.open(file) for file in data_links]
                except Exception:
                    print(
                        "An exception occurred while trying to access remote files via HTTPS: "
                        f"Exception: {traceback.format_exc()}"
                    )
                    return None
            return fileset

    @_open.register
    def _open_urls(
        self,
        granules: List[str],
        provider: Optional[str] = None,
    ) -> Union[List[Any], None]:

        fileset: List = []
        data_links: List = []

        if isinstance(granules[0], str) and (
            granules[0].startswith("s3") or granules[0].startswith("http")
        ):
            # TODO: method to derive the DAAC from url?
            provider = provider
            data_links = granules
        else:
            print(
                f"Schema for {granules[0]} is not recognized, must be an HTTP or S3 URL"
            )
            return None
        if self.auth is None:
            print(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )
            return None

        if self.running_in_aws:
            s3_fs = self.get_s3fs_session(provider=provider)
            if s3_fs is not None:
                try:
                    fileset = [s3_fs.open(file) for file in data_links]
                except Exception:
                    print(
                        "An exception occurred while trying to access remote files on S3: "
                        "This may be caused by trying to access the data outside the us-west-2 region"
                        f"Exception: {traceback.format_exc()}"
                    )
                    return None
            return fileset
        else:
            https_fs = self.get_fsspec_session()
            if https_fs is not None:
                try:
                    fileset = [https_fs.open(file) for file in data_links]
                except Exception:
                    print(
                        "An exception occurred while trying to access remote files via HTTPS: "
                        f"Exception: {traceback.format_exc()}"
                    )
                    return None
            return fileset

    def get(
        self,
        granules: Union[List[DataGranule], List[str]],
        local_path: Optional[str] = None,
        provider: Optional[str] = None,
        threads: int = 8,
    ) -> Union[None, List[str]]:
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
        if len(granules):
            files = self._get(granules, local_path, provider, threads)
            return files
        else:
            print("List of URLs or DataGranule isntances expected")
            return None

    @singledispatchmethod
    def _get(
        self,
        granules: Union[List[DataGranule], List[str]],
        local_path: Optional[str] = None,
        provider: Optional[str] = None,
        threads: int = 8,
    ) -> Union[None, List[str]]:
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
        print("List of URLs or DataGranule isntances expected")
        return None

    @_get.register
    def _get_urls(
        self,
        granules: List[str],
        local_path: Optional[str] = None,
        provider: Optional[str] = None,
        threads: int = 8,
    ) -> Union[None, List[str]]:

        data_links = granules
        downloaded_files: List = []
        if provider is None and self.running_in_aws and "cumulus" in data_links[0]:
            print(
                "earthaccess can't yet guess the provider for cloud collections, "
                "we need to use one from earthaccess.list_cloud_providers()"
            )
            return None
        if self.running_in_aws:
            print(f"Accessing cloud dataset using provider: {provider}")
            s3_fs = self.get_s3fs_session(provider=provider)
            # TODO: make this parallel or concurrent
            for file in data_links:
                file_name = file.split("/")[-1]
                s3_fs.get(file, local_path)
                print(f"Retrieved: {file} to {local_path}")
                downloaded_files.append(file_name)
            return downloaded_files

        else:
            # if we are not in AWS
            return self._download_onprem_granules(data_links, local_path, threads)
        return None

    @_get.register
    def _get_granules(
        self,
        granules: List[DataGranule],
        local_path: Optional[str] = None,
        provider: Optional[str] = None,
        threads: int = 8,
    ) -> Union[None, List[str]]:

        data_links: List = []
        downloaded_files: List = []
        provider = granules[0]["meta"]["provider-id"]
        cloud_hosted = granules[0].cloud_hosted
        access = "direc" if (cloud_hosted and self.running_in_aws) else "external"
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
            print(f"Accessing cloud dataset using provider: {provider}")
            s3_fs = self.get_s3fs_session(provider)
            # TODO: make this async
            for file in data_links:
                s3_fs.get(file, local_path)
                file_name = file.split("/")[-1]
                print(f"Retrieved: {file} to {local_path}")
                downloaded_files.append(file_name)
            return downloaded_files
        else:
            # if the data is cloud based bu we are not in AWS it will be downloaded as if it was on prem
            return self._download_onprem_granules(data_links, local_path, threads)
        return None

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
                session = self.auth.get_session(False)
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
        return local_filename

    def _download_onprem_granules(
        self, urls: List[str], directory: Optional[str] = None, threads: int = 8
    ) -> List[Any]:
        """
        downloads a list of URLS into the data directory.
        :param urls: list of granule URLs from an on-prem collection
        :param directory: local directory to store the files
        :param threads: parallel number of threads to use to download the files, adjust as necessary, default = 8
        :returns: None
        """
        if urls is None:
            print("The granules didn't provide a valid GET DATA link")
            return None
        if self.auth is None:
            print(
                "We need to be logged into NASA EDL in order to download data granules"
            )
            return []
        if directory is None:
            directory_prefix = f"./data/{datetime.datetime.today().strftime('%Y-%m-%d')}-{uuid4().hex[:6]}"
        else:
            directory_prefix = directory
        if not os.path.exists(directory_prefix):
            os.makedirs(directory_prefix)

        arguments = [(url, directory_prefix) for url in urls]
        results = pqdm(
            arguments,
            self._download_file,
            n_jobs=threads,
            argument_type="args",
        )
        return results
