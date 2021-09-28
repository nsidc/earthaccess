import datetime
import os
from typing import Any, List, Union
from uuid import uuid4

import s3fs
from pqdm.threads import pqdm

from .results import DataGranule


class Accessor(object):
    """
    Accessor class for data granules, on prem or in the cloud.
    """

    def _is_valid(self, granules: List[Any]) -> bool:
        return False

    def __init__(self, auth: Any) -> None:
        self.auth = auth

    def _get_s3_session(self, provider: str) -> Any:
        s3_credentials = self.auth.get_s3_credentials(provider)
        s3_fs = s3fs.S3FileSystem(
            key=s3_credentials["accessKeyId"],
            secret=s3_credentials["secretAccessKey"],
            token=s3_credentials["sessionToken"],
        )
        return s3_fs

    def open(self, granules: List[Any]) -> List[Any]:
        """
        returns a list of S3 file objects that can be used to access files
        hosted on S3 by third party libraries like xarray
        """
        if not (len(granules) > 0 and isinstance(granules[0], DataGranule)):
            return []
        provider = granules[0]["meta"]["provider-id"]
        cloud_hosted = granules[0].cloud_hosted
        if not cloud_hosted:
            print("Can't open files that are not cloud hosted, try with .get()")
            return []
        s3_fs = self._get_s3_session(provider)
        # We are assuming that the first GET DATA link is the data link
        # TODO: filter by file type?
        data_links = [granule.data_links()[0] for granule in granules]
        try:
            fileset = [s3_fs.open(file) for file in data_links]
        except Exception as e:
            print(
                "An exception occurred while trying to access remote files on S3: "
                "This may be caused by trying to access the data outside the us-west-2 region"
                f"Exception: {e}"
            )
        return fileset

    def get(
        self, granules: List[Any], local_path: str = "./data"
    ) -> Union[None, List[str]]:

        provider = granules[0]["meta"]["provider-id"]
        cloud_hosted = granules[0].cloud_hosted
        data_links = [granule.data_links()[0] for granule in granules]
        if cloud_hosted:
            s3_fs = self._get_s3_session(provider)
            # TODO: make this parallel
            for file in data_links:
                s3_fs.get(file, local_path)
                print(f"Downloaded: {file} to {local_path}")
        else:
            self._download_onprem_granules(data_links, local_path)
        return None

    def _download_file(self, url: str, directory: str, file_paths: List[str]) -> str:
        local_filename = url.split("/")[-1]
        # NOTE the stream=True parameter below
        if not os.path.exists(f"{directory}/{local_filename}"):
            with self.auth.session.get(url, stream=True) as r:
                r.raise_for_status()
                with open(f"{directory}/{local_filename}", "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                file_paths.append(local_filename)
        return local_filename

    def _download_onprem_granules(
        self, urls: List[str], path_prefix: str = None, threads: int = 4
    ) -> Union[None, List[str]]:
        """
        downloads a list of URLS into the data directory.
        and dumps the current parameters to help identify the files later on.
        params:
            - urls: array of ITS_LIVE urls
            - path_prefix: directory on which the files will be downloaded.
        returns:
           - array: list of the downloaded files
        """
        if path_prefix is None:
            directory_prefix = f"data/{datetime.datetime.today().strftime('%Y-%m-%d')}-{uuid4().hex[:6]}"
        else:
            directory_prefix = path_prefix
        if not os.path.exists(directory_prefix):
            os.makedirs(directory_prefix)

        if urls is None:
            return None
        if self.auth is None:
            print(
                "We need to be logged into NASA EDL in order to download data granules"
            )
            return None
        file_paths: List = []
        arguments = [(url, directory_prefix, file_paths) for url in urls]
        result = pqdm(
            arguments, self._download_file, n_jobs=threads, argument_type="args"
        )
        if result is None:
            pass

        return file_paths
