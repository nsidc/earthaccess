import datetime
import os
import shutil
import traceback
from copy import deepcopy
from itertools import chain
from typing import Any, List, Union
from uuid import uuid4

import aiohttp
import fsspec
import s3fs
from pqdm.threads import pqdm

from .daac import find_provider
from .results import DataGranule
from .search import DataCollections


class Store(object):
    """
    Store class to access granules on-prem or in the cloud.
    """

    def __init__(self, auth: Any) -> None:
        if auth.authenticated is True:
            self.auth = auth
            # Async operation warning, in a notebook we're already using async
            self.jar = aiohttp.CookieJar(unsafe=True)
            fsspec.config.conf["https"] = dict(
                client_kwargs={
                    "auth": aiohttp.BasicAuth(
                        self.auth._credentials[0], self.auth._credentials[1]
                    ),
                    "cookie_jar": self.jar,
                }
            )
            self.s3_fs = None
            self.initial_ts = datetime.datetime.now()
        else:
            print("Warning: the current session is not authenticated with NASA")
            self.auth = None

    def _derive_concept_provider(self, concept_id: str = None) -> str:
        if concept_id is not None:
            provider = concept_id.split("-")[1]
            return provider
        return ""

    def _derive_daac_provider(self, daac: str = None) -> Union[str, None]:
        provider = find_provider(daac, True)
        return provider

    def _is_cloud_collection(self, concept_id: str = None) -> bool:
        collection = DataCollections(self.auth).concept_id(concept_id).get()
        if len(collection) > 0 and "s3-links" in collection[0]["meta"]:
            return True
        return False

    def get_s3fs_session(
        self, daac: str = None, concept_id: str = None, provider: str = None
    ) -> s3fs.S3FileSystem:
        """
        Returns a s3fs instance for a given cloud provider / DAAC
        :param daac: any of the DAACs e.g. NSIDC, PODAAC
        :returns: a s3fs instance
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
            if self.s3_fs is None or round(delta_minutes.seconds / 60, 2) > 59:
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

    def get_https_session(
        self, bearer_token: bool = False
    ) -> fsspec.AbstractFileSystem:
        """
        Returns a FSSPEC HTTPS session with bearer tokens that are used by CMR.
        This HTTPS session can be used to download granules if we want to use a direct, lower level API
        :returns: FSSPEC HTTPFileSystem (aiohttp client session)
        """
        session = fsspec.filesystem("https")
        if bearer_token and self.auth.authenticated:
            session.headers[
                "Authorization"
            ] = f'Bearer {self.auth.token["access_token"]}'
        return session

    def open(
        self, granules: List[Any], provider: str = None, direct_access: bool = False
    ) -> List[Any]:
        """
        returns a list of fsspec file-like objects that can be used to access files
        hosted on S3 or HTTPS by third party libraries like xarray.

        :param granules: a list of granules(DataGranule) instances or list of files
        :param provider: cloud provider code, used when the list is made of s3 links
        :returns: a list of s3fs "file pointers" to s3 files
        """
        fileset: List = []
        data_links: List = []
        if isinstance(granules[0], DataGranule):
            provider = granules[0]["meta"]["provider-id"]
            data_links = list(
                chain.from_iterable(
                    granule.data_links(access="direct") for granule in granules
                )
            )
            total_size = round(sum([granule.size() for granule in granules]) / 1024, 2)
            print(
                f" Getting {len(granules)} granules, approx download size: {total_size} GB"
            )
        elif isinstance(granules[0], str) and (
            granules[0].startswith("s3") or granules[0].startswith("http")
        ):
            # TODO: cleaver method to derive the DAAC from url?
            provider = provider
            data_links = granules
        if self.auth is None:
            print(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )
            return []

        if direct_access:
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
            return fileset
        else:
            https_fs = self.get_https_session()
            if https_fs is not None:
                try:
                    fileset = [https_fs.open(file) for file in data_links]
                except Exception:
                    print(
                        "An exception occurred while trying to access remote files via HTTPS: "
                        f"Exception: {traceback.format_exc()}"
                    )
            return fileset

    def get(
        self,
        granules: List[Any],
        local_path: str = None,
        access: str = None,
        provider: str = None,
        threads: int = 8,
    ) -> None:
        """
        Retrieves data granules from a remote storage system.
        If we run this in the cloud we are moving data from S3 to a cloud compute instance (EC2, AWS Lambda)
        If we run it outside the us-west-2 region and the data granules are part of a cloud-based collection
        the method will not get any files.
        If we requests data granules from an on-prem collection the data will be effectively downloaded
        to a local directory.

        :param granules: a list of granules(DataGranule) instances or a list of granule links (HTTP)
        :param local_path: local directory to store the remote data granules
        :param access: direct or onprem, if set it will use it for the access method.
        :param threads: parallel number of threads to use to download the files, adjust as necessary, default = 8
        :returns: None
        """
        data_links: List = []
        if isinstance(granules[0], DataGranule):
            provider = granules[0]["meta"]["provider-id"]
            cloud_hosted = granules[0].cloud_hosted
            if cloud_hosted and access is None:
                # TODO: validate that we are in us-west-2
                access = "direct"
            if not cloud_hosted and access is None:
                access = "on_prem"
            data_links = list(
                chain.from_iterable(
                    granule.data_links(access=access) for granule in granules
                )
            )
            total_size = round(sum([granule.size() for granule in granules]) / 1024, 2)
            print(
                f" Getting {len(granules)} granules, approx download size: {total_size} GB"
            )
        elif isinstance(granules[0], str) and granules[0].startswith("http"):
            provider = provider
            data_links = granules
        if access == "direct":
            print(f"Accessing cloud dataset using provider: {provider}")
            s3_fs = self.get_s3fs_session(provider)
            # TODO: make this parallel or concurrent
            for file in data_links:
                s3_fs.get(file, local_path)
                print(f"Retrieved: {file} to {local_path}")
        else:
            # if the data is cloud based bu we are not in AWS it will be downloaded as if it was on prem
            self._download_onprem_granules(data_links, local_path, threads)
        return None

    def _download_file(self, url: str, directory: str) -> str:
        """
        download a single file from an on-prem location, a DAAC data center.
        :param url: the granule url
        :param directory: local directory
        :returns: local filepath or an exception
        """
        # If the get data link is an Opendap location
        if "/opendap/" in url and url.endswith(".nc.html"):
            url = url.replace(".html", "")
        local_filename = url.split("/")[-1]
        if not os.path.exists(f"{directory}/{local_filename}"):
            try:
                # TODO: make this efficient using cache
                session = self.get_https_session()
                r = session.head(url)
                if "Content-Type" in r.headers:
                    if "text/html" in r.headers["Content-Type"]:
                        print(
                            f"Granule file is not resolving to a valid location: {url}"
                        )
                        return ""
                with session.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(f"{directory}/{local_filename}", "wb") as f:
                        # This is to cap memory usage for large files at 1MB per write to disk per thread
                        # https://docs.python-requests.org/en/master/user/quickstart/#raw-response-content
                        shutil.copyfileobj(r.raw, f, length=1024 * 1024)
            except Exception:
                print(f"Error while downloading the file {local_filename}")
                print(traceback.format_exc())
                raise
        else:
            print(f"File {local_filename} already downloaded")
        return local_filename

    def _download_cloud_granules(
        self, urls: List[str], directory: str = None, threads: int = 8
    ) -> None:
        return None

    def _download_onprem_granules(
        self, urls: List[str], directory: str = None, threads: int = 8
    ) -> None:
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
            return None
        if directory is None:
            directory_prefix = f"./data/{datetime.datetime.today().strftime('%Y-%m-%d')}-{uuid4().hex[:6]}"
        else:
            directory_prefix = directory
        if not os.path.exists(directory_prefix):
            os.makedirs(directory_prefix)

        arguments = [(url, directory_prefix) for url in urls]
        result = pqdm(
            arguments, self._download_file, n_jobs=threads, argument_type="args"
        )
        if result is None:
            pass
        return
