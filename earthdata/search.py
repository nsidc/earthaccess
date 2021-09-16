from typing import Any, List, Type

from cmr import CollectionQuery, GranuleQuery  # type: ignore
from IPython.display import display
from requests import exceptions

from .auth import Auth
from .results import DataCollection, DataGranule


class DataCollections(CollectionQuery):
    _fields = None
    _format = "umm_json"

    def __init__(self, auth: Type[Auth] = None, *args: Any, **kwargs: Any) -> None:
        self._auth = auth
        super().__init__(*args, **kwargs)
        self.params["has_granules"] = True
        self.params["include_granule_counts"] = True

    def fields(self, fields: List[str] = None) -> Type[CollectionQuery]:
        self._fields = fields
        return self

    def display(self, limit: int = 20, fields: List[str] = None) -> None:
        if limit > 20:
            limit = 20
        collections = self.get(limit)
        [display(collection) for collection in collections]

    def cloud_hosted(self, cloud_hosted: bool = True) -> Type[CollectionQuery]:
        """
        Only match granules that are hosted in the cloud.
        :param cloud_only: True to require granules only be online
        :returns: Query instance
        """

        if not isinstance(cloud_hosted, bool):
            raise TypeError("Online_only must be of type bool")

        self.params["cloud_hosted"] = cloud_hosted
        return self

    def get(self, limit: int = 2000) -> list:
        """
        Get all results up to some limit, even if spanning multiple pages.
        :limit: The number of results to return
        :returns: query results as a list
        """

        page_size = min(limit, 2000)
        url = self._build_url()

        results: List = []
        page = 1
        while len(results) < limit:
            params = {"page_size": page_size, "page_num": page}
            if self._token is not None:
                params["token"] = self._token

            response = self.session.get(url, params=params)

            try:
                response.raise_for_status()
            except exceptions.HTTPError as ex:
                raise RuntimeError(ex.response.text)

            if self._format == "json":
                latest = response.json()["feed"]["entry"]
            elif self._format == "umm_json":
                latest = list(
                    DataCollection(collection, self._fields)
                    for collection in response.json()["items"]
                )
            else:
                latest = [response.text]

            if len(latest) == 0:
                break

            results.extend(latest)
            page += 1

        return results


class DataGranules(GranuleQuery):
    """
    A Granule oriented client for NASA CMR API
    API: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
    """

    _format = "umm_json"
    _valid_formats_regex = [
        "json",
        "xml",
        "echo10",
        "iso",
        "iso19115",
        "csv",
        "atom",
        "kml",
        "native",
        "umm_json",
    ]

    def __init__(self, auth: Type[Auth] = None, *args: Any, **kwargs: Any) -> None:
        self._auth = auth
        super().__init__(*args, **kwargs)

    def _valid_state(self) -> bool:

        # spatial params must be paired with a collection limiting parameter
        spatial_keys = ["point", "polygon", "bounding_box", "line"]
        collection_keys = ["short_name", "entry_title", "concept_id"]

        if any(key in self.params for key in spatial_keys):
            if not any(key in self.params for key in collection_keys):
                return False

        # all good then
        return True

    def display(self, limit: int = 20) -> list:
        """"""
        granules = self.get(limit)
        [display(granule) for granule in granules]
        return granules

    def get(self, limit: int = 2000) -> list:
        """
        Get all results up to some limit, even if spanning multiple pages.
        :limit: The number of results to return
        :returns: query results as a list
        """

        page_size = min(limit, 2000)
        url = self._build_url()

        results: List = []
        page = 1
        # TODO: implement LRU cache and offsets
        while len(results) < limit:
            params = {"page_size": page_size, "page_num": page}
            if self._token is not None:
                params["token"] = self._token

            response = self.session.get(url, params=params)

            try:
                response.raise_for_status()
            except exceptions.HTTPError as ex:
                raise RuntimeError(ex.response.text)

            if self._format == "json":
                latest = response.json()["feed"]["entry"]
            elif self._format == "umm_json":
                latest = list(
                    DataGranule(granule) for granule in response.json()["items"]
                )
            else:
                latest = [response.text]

            if len(latest) == 0:
                break

            results.extend(latest)
            page += 1

        return results
