import datetime as dt
from typing import Any, List, Type

import dateutil.parser as parser  # type: ignore
from cmr import CollectionQuery, GranuleQuery  # type: ignore
from requests import exceptions, session

from .daac import CLOUD_PROVIDERS, DAACS
from .results import DataCollection, DataGranule


class DataCollections(CollectionQuery):
    _fields = None
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

    def __init__(self, auth: Any = None, *args: Any, **kwargs: Any) -> None:
        """
        The DataCollection class queries against https://cmr.earthdata.nasa.gov/search/collections.umm_json
        by default, the response has to be in umm_json in order to use the result classes.
        :param auth: an Auth class instance in case we want to query protected collections
        """
        super().__init__(*args, **kwargs)
        if auth is not None and auth.authenticated:
            # To search we need the new bearer tokens from NASA Earthdata
            self.session = auth.get_session(bearer_token=True)
        else:
            self.session = session()

        self._debug = False

        self.params["has_granules"] = True
        self.params["include_granule_counts"] = True

    def __find_provider(
        self, daac_short_name: str = None, cloud_hosted: bool = None
    ) -> str:
        for daac in DAACS:
            if daac_short_name == daac["short-name"]:
                if cloud_hosted:
                    if len(daac["cloud-providers"]) > 0:
                        return daac["cloud-providers"][0]
                    else:
                        # We found the DAAC but it does not have cloud data
                        return daac["on-prem-providers"][0]
                else:
                    return daac["on-prem-providers"][0]
        return ""

    def print_help(self, method: str = "fields") -> None:
        print("Class components: \n")
        print([method for method in dir(self) if method.startswith("_") is False])
        help(getattr(self, method))

    def fields(self, fields: List[str] = None) -> Type[CollectionQuery]:
        """
        Masks the response by only showing the fields included in this list
        """
        self._fields = fields
        return self

    def debug(self, debug: bool = True) -> Type[CollectionQuery]:
        """
        If True, prints the actual query to CMR
        """
        self._debug = True
        return self

    def cloud_hosted(self, cloud_hosted: bool = True) -> Type[CollectionQuery]:
        """
        Only match granules that are hosted in the cloud.
        :param cloud_only: True to require granules only be online
        :returns: Query instance
        """
        if not isinstance(cloud_hosted, bool):
            raise TypeError("cloud_hosted must be of type bool")

        self.params["cloud_hosted"] = cloud_hosted
        if hasattr(self, "DAAC"):
            provider = self.__find_provider(self.DAAC, cloud_hosted)
            self.params["provider"] = provider
        return self

    def provider(self, provider: str = "") -> Type[CollectionQuery]:
        """
        Only match collections from a given provider, a NASA datacenter or DAAC can have 1 or more providers
        i.e. PODAAC is a data center or DAAC, PODAAC is the default provider for on prem data, POCLOUD is
        the PODAAC provider for their data in the cloud.
        """
        self.params["provider"] = provider
        return self

    def data_center(self, data_center_name: str = "") -> Type[CollectionQuery]:
        """
        just another name for the DAAC, so is more intuitive.
        """
        return self.daac(data_center_name)

    def daac(self, daac_short_name: str = "") -> Type[CollectionQuery]:
        """
        Only match collections for a given DAAC, by default the on-prem collections for the DAAC
        """
        if "cloud_hosted" in self.params:
            cloud_hosted = self.params["cloud_hosted"]
        else:
            cloud_hosted = False
        self.DAAC = daac_short_name
        self.params["provider"] = self.__find_provider(daac_short_name, cloud_hosted)
        return self

    def get(self, limit: int = 2000) -> list:
        """
        Get all results up to some limit, even if spanning multiple pages.
        :param limit: The number of results to return
        :returns: query results as a list
        """

        page_size = min(limit, 200)
        url = self._build_url()

        results: List = []
        page = 1
        while len(results) < limit:
            params = {"page_size": page_size, "page_num": page}
            if self._debug:
                print(f"Fetching: {url}")
            # TODO: implement caching
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

    def temporal(
        self, date_from: str, date_to: str, exclude_boundary: bool = False
    ) -> Type[CollectionQuery]:
        """
        Filter by an open or closed date range.
        Dates can be provided as a datetime objects or ISO 8601 formatted strings. Multiple
        ranges can be provided by successive calls to this method before calling execute().
        :param date_from: earliest date of temporal range
        :param date_to: latest date of temporal range
        :param exclude_boundary: whether or not to exclude the date_from/to in the matched range
        :returns: GranueQuery instance
        """
        DEFAULT = dt.datetime(1979, 1, 1)
        if date_from is not None:
            try:
                parsed_from = parser.parse(date_from, default=DEFAULT).isoformat() + "Z"
            except Exception:
                print("The provided start date was not recognized")
                parsed_from = ""
        if date_to is not None:
            try:
                parsed_to = parser.parse(date_to, default=DEFAULT).isoformat() + "Z"
            except Exception:
                print("The provided end date was not recognized")
                parsed_to = ""
        super().temporal(parsed_from, parsed_to, exclude_boundary)
        return self


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

    def __init__(self, auth: Any = None, *args: Any, **kwargs: Any) -> None:
        """"""
        super().__init__(*args, **kwargs)
        if auth is not None and auth.authenticated:
            # To search we need the new bearer tokens from NASA Earthdata
            self.session = auth.get_session(bearer_token=True)
        else:
            self.session = session()

        self._debug = False

    def _valid_state(self) -> bool:

        # spatial params must be paired with a collection limiting parameter
        spatial_keys = ["point", "polygon", "bounding_box", "line"]
        collection_keys = ["short_name", "entry_title", "concept_id"]

        if any(key in self.params for key in spatial_keys):
            if not any(key in self.params for key in collection_keys):
                return False

        # all good then
        return True

    def _is_cloud_hosted(self, granule: Any) -> bool:
        if granule["meta"]["provider-id"] in CLOUD_PROVIDERS:
            data_url = granule["umm"]["RelatedUrls"][0]["URL"]
            if "cumulus" in data_url:
                return True
        return False

    def get(self, limit: int = 20000) -> list:
        """
        Get all results up to some limit, even if spanning multiple pages.
        :limit: The number of results to return
        :returns: query results as a list
        """
        # TODO: implement caching and scroll
        page_size = min(limit, 2000)
        url = self._build_url()

        results: List = []
        page = 1
        while len(results) < limit:
            params = {"page_size": page_size, "page_num": page}
            # TODO: should be in a logger
            if self._debug:
                print(f"Fetching: {url}")

            response = self.session.get(url, params=params)

            try:
                response.raise_for_status()
            except exceptions.HTTPError as ex:
                raise RuntimeError(ex.response.text)

            if self._format == "json":
                latest = response.json()["feed"]["entry"]
            elif self._format == "umm_json":
                json_response = response.json()["items"]
                if len(json_response) > 0:
                    if self._is_cloud_hosted(json_response[0]):
                        cloud = True
                    else:
                        cloud = False
                    latest = list(
                        DataGranule(granule, cloud_hosted=cloud)
                        for granule in response.json()["items"]
                    )
                else:
                    latest = []
            else:
                latest = [response.text]

            if len(latest) == 0:
                break

            results.extend(latest)
            page += 1

        return results

    def debug(self, debug: bool = True) -> Type[GranuleQuery]:
        self._debug = True
        return self

    def temporal(
        self, date_from: str = None, date_to: str = None, exclude_boundary: bool = False
    ) -> Type[GranuleQuery]:
        """
        Filter by an open or closed date range.
        Dates can be provided as a datetime objects or ISO 8601 formatted strings. Multiple
        ranges can be provided by successive calls to this method before calling execute().
        :param date_from: earliest date of temporal range
        :param date_to: latest date of temporal range
        :param exclude_boundary: whether or not to exclude the date_from/to in the matched range
        :returns: GranueQuery instance
        """
        DEFAULT = dt.datetime(1979, 1, 1)
        if date_from is not None:
            try:
                parsed_from = parser.parse(date_from, default=DEFAULT).isoformat() + "Z"
            except Exception:
                print("The provided start date was not recognized")
                parsed_from = ""
        if date_to is not None:
            try:
                parsed_to = parser.parse(date_to, default=DEFAULT).isoformat() + "Z"
            except Exception:
                print("The provided end date was not recognized")
                parsed_to = ""
        super().temporal(parsed_from, parsed_to, exclude_boundary)
        return self
