import datetime
import os
import shutil
import traceback
from typing import Any, List
from uuid import uuid4

import s3fs
from pqdm.threads import pqdm

from .results import DataGranule


class Accessor(object):
    """
    Accessor class for data granules, on prem or in the cloud.
    """

    def _is_valid(self, granules: List[Any]) -> bool:
        """
        When implemented verify that the list contains granules from only one collection
        """
        return False

    def __init__(self, auth: Any) -> None:
        if auth.authenticated is True:
            self.auth = auth
        else:
            self.auth = None

    def _get_s3_filesystem(self, provider: str) -> Any:
        """
        get a s3fs intance for a given cloud provider
        :param provider: any of the DAAC cloud providers e.g. POCLOUD
        :returns: a new s3fs instance
        """
        if self.auth is not None:
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

    def open(self, granules: List[Any]) -> List[Any]:
        """
        returns a list of S3 file objects that can be used to access files
        hosted on S3 by third party libraries like xarray
        :param granules: a list of granules(DataGranule) instances
        :returns: a list of s3fs "file pointers" to s3 files
        """
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
        s3_fs = self._get_s3_filesystem(provider)
        # We are assuming that the first GET DATA link is the data link
        # TODO: filter by file type?
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
        self, granules: List[Any], local_path: str = None, threads: int = 8
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
        :param threads: parallel number of threads to use to download the files, adjust as necessary, default = 8
        :returns: None
        """

        provider = granules[0]["meta"]["provider-id"]
        cloud_hosted = granules[0].cloud_hosted
        data_links = [granule.data_links()[0] for granule in granules]
        if cloud_hosted:
            s3_fs = self._get_s3_filesystem(provider)
            # TODO: make this parallel
            for file in data_links:
                s3_fs.get(file, local_path)
                print(f"Retrieved: {file} to {local_path}")
        else:
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
                session = self.auth.get_session()
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
