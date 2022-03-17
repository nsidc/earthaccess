import datetime
import os
import shutil
import traceback
from typing import Any, List, Union
from uuid import uuid4

import s3fs
from pqdm.threads import pqdm

from .auth import SessionWithHeaderRedirection
from .results import DataGranule
from .search import DataCollections


class Store(object):
    """
    Store class to access granules on prem or in the cloud.
    """

    def __init__(self, auth: Any) -> None:
        if auth.authenticated is True:
            self.auth = auth
        else:
            self.auth = None

    def _derive_provider(self, concept_id: str = None) -> str:
        if concept_id is not None:
            provider = concept_id.split("-")[1]
            return provider
        return ""

    def _is_cloud_collection(self, concept_id: str = None) -> bool:
        collection = DataCollections(self.auth).concept_id(concept_id).get()
        if len(collection) > 0 and "s3-links" in collection[0]["meta"]:
            return True
        return False

    def get_file_session(
        self,
        granules: List[Any] = None,
        concept_id: str = None,
        cloud_access: bool = False,
    ) -> Union[SessionWithHeaderRedirection, s3fs.S3FileSystem]:
        """
        if the collection is a cloud collection our file session will be a s3fs session,
        if the collection is hosted by a DAAC, our session will be an https session.
        """
        if granules is not None and len(granules) > 0:
            cloud_hosted = granules[0].cloud_hosted
            provider = granules[0]["meta"]["provider-id"]
        if concept_id is not None:
            cloud_hosted = self._is_cloud_collection(concept_id)
            provider = self._derive_provider(concept_id)
        if cloud_hosted and cloud_access:
            return self.get_s3fs_session(provider=provider)
        elif cloud_hosted and cloud_access is False:
            return self.get_http_session()
        return self.get_http_session()

    def get_s3fs_session(
        self, provider: str = None, concept_id: str = None
    ) -> s3fs.S3FileSystem:
        """
        get a s3fs instance for a given cloud provider
        :param provider: any of the DAAC cloud providers e.g. POCLOUD
        :returns: a new s3fs instance
        """
        if self.auth is not None:
            if concept_id is not None:
                provider = self._derive_provider(concept_id)
            s3_credentials = self.auth.get_s3_credentials(provider)
            s3_fs = s3fs.S3FileSystem(
                key=s3_credentials["accessKeyId"],
                secret=s3_credentials["secretAccessKey"],
                token=s3_credentials["sessionToken"],
            )
            return s3_fs
        else:
            print(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )
            return None

    def get_http_session(
        self, bearer_token: bool = False
    ) -> SessionWithHeaderRedirection:
        """
        returns a new request session instance, since looks like using a session in a context is not threadsafe
        https://github.com/psf/requests/issues/1871
        Session with bearer tokens are used by CMR, simple auth sessions can be used do download data
        from on-prem DAAC data centers.
        :returns: subclass SessionWithHeaderRedirection instance
        """
        if bearer_token and self.auth.authenticated:
            session = SessionWithHeaderRedirection()
            session.headers.update(
                {"Authorization": f'Bearer {self.auth.token["access_token"]}'}
            )
            return session
        else:
            return SessionWithHeaderRedirection(
                self.auth._credentials[0], self.auth._credentials[1]
            )

    def open(self, granules: List[Any]) -> List[Any]:
        """
        returns a list of S3 file objects that can be used to access files
        hosted on S3 by third party libraries like xarray
        :param granules: a list of granules(DataGranule) instances
        :returns: a list of s3fs "file pointers" to s3 files
        """
        fileset: List
        if self.auth is None:
            print(
                "A valid Earthdata login instance is required to retrieve S3 credentials"
            )
            return []

        if not (len(granules) > 0 and isinstance(granules[0], DataGranule)):
            print("To open a dataset a valid list of DataGranule instances is needed")
            return []
        provider = granules[0]["meta"]["provider-id"]
        cloud_hosted = granules[0].cloud_hosted
        if not cloud_hosted:
            print("Can't open files that are not cloud hosted, try with .get()")
            return []
        s3_fs = self.get_s3fs_session(provider=provider)
        # We are assuming that the first GET DATA link is the data link
        # TODO: filter by file type?
        if s3fs is not None:
            data_links = [granule.data_links()[0] for granule in granules]
            try:
                fileset = [s3_fs.open(file) for file in data_links]
            except Exception:
                print(
                    "An exception occurred while trying to access remote files on S3: "
                    "This may be caused by trying to access the data outside the us-west-2 region"
                    f"Exception: {traceback.format_exc()}"
                )
        return fileset

    def get(
        self,
        granules: List[Any],
        local_path: str = None,
        direct_access: bool = True,
        provider: str = None,
        threads: int = 8,
    ) -> None:
        """
        Retrieves data granules from a remote storage system to a local instance.
        If we run this in the cloud we are moving data from S3 to a cloud compute instance (EC2, AWS Lambda)
        If we run it outside the us-west-2 region and the data granules are part of a cloud-based collection
        the method will not get any files.
        If we requests data granules from an on-prem collection the data will be effectively downloaded
        to a local directory.

        :param granules: a list of granules(DataGranule) instances
        :param local_path: local directory to store the remote data granules
        :param direct_access: use direct S3 access, only possible for cloud collections if the code runs on us-west-2
        :param threads: parallel number of threads to use to download the files, adjust as necessary, default = 8
        :returns: None
        """
        data_links: List = []
        if isinstance(granules[0], DataGranule):
            provider = granules[0]["meta"]["provider-id"]
            cloud_hosted = granules[0].cloud_hosted
            data_links = [
                granule.data_links(s3_only=direct_access)[0] for granule in granules
            ]
            total_size = round(sum([granule.size() for granule in granules]) / 1024, 2)
            print(
                f" Getting {len(granules)} granules, approx download size: {total_size} GB"
            )
        elif isinstance(granules[0], str):
            # TODO: Fix this!
            provider = provider
            data_links = granules
            cloud_hosted = direct_access
        if cloud_hosted and direct_access:
            s3_fs = self.get_s3fs_session(provider)
            # TODO: make this parallel
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
        local_filename = url.split("/")[-1]
        if not os.path.exists(f"{directory}/{local_filename}"):
            try:
                # Looks like requests.session is not threadsafe
                # TODO: make this efficient
                session = self.get_http_session()
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
