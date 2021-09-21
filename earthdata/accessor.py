from typing import Any, List

import s3fs

from .results import DataGranule


class Accessor(object):
    """
    Accessor class for data granules, on prem or in the cloud.
    """

    def _is_valid(self, granules: List[Any]) -> bool:
        return False

    def __init__(self, auth: Any) -> None:
        self.auth = auth

    def get_s3_session(self, provider: str) -> Any:
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
        s3_fs = self.get_s3_session(provider)
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

    def get(self, granules: List[Any], local_path: str = "./data") -> None:

        provider = granules[0]["meta"]["provider-id"]
        cloud_hosted = granules[0].cloud_hosted
        if cloud_hosted:
            s3_fs = self.get_s3_session(provider)
            data_links = [granule.data_links()[0] for granule in granules]
            # TODO: make this parallel
            for file in data_links:
                s3_fs.get(file, local_path)
                print(f"Downloaded: {file} to {local_path}")
        else:
            #
            return None
        return None
