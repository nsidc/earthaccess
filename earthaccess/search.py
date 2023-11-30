import datetime as dt
from inspect import getmembers, ismethod
from typing import Any, Dict, List, Optional, Tuple, Type

import dateutil.parser as parser  # type: ignore
from cmr import CollectionQuery, GranuleQuery  # type: ignore
from requests import exceptions, session

from .auth import Auth
from .daac import find_provider, find_provider_by_shortname
from .results import DataCollection, DataGranule


class DataCollections(CollectionQuery):
    """
    ???+ Info
        The DataCollection class queries against https://cmr.earthdata.nasa.gov/search/collections.umm_json,
        the response has to be in umm_json in order to use the result classes.
    """

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

    def __init__(self, auth: Optional[Auth] = None, *args: Any, **kwargs: Any) -> None:
        """Builds an instance of DataCollections to query CMR

        Parameters:
            auth (Auth): An authenticated `Auth` instance, this is an optional parameter
                for queries that need authentication e.g. restricted datasets
        """
        super().__init__(*args, **kwargs)
        self.session = session()
        if auth is not None and auth.authenticated:
            # To search we need the new bearer tokens from NASA Earthdata
            self.session = auth.get_session(bearer_token=True)

        self._debug = False

        self.params["has_granules"] = True
        self.params["include_granule_counts"] = True

    def hits(self) -> int:
        """Returns the number of hits the current query will return. This is done by
        making a lightweight query to CMR and inspecting the returned headers.
        Restricted datasets will always return 0 results even if there are results.


        Returns:
            number of results reported by CMR
        """
        return super().hits()

    def concept_id(self, IDs: List[str]) -> Type[CollectionQuery]:
        """Filter by concept ID (ex: C1299783579-LPDAAC_ECS or G1327299284-LPDAAC_ECS, S12345678-LPDAAC_ECS)

        Collections, granules, tools, services are uniquely identified with this ID.
        >
        * If providing a collection's concept ID here, it will filter by granules associated with that collection.
        * If providing a granule's concept ID here, it will uniquely identify those granules.
        * If providing a tool's concept ID here, it will uniquely identify those tools.
        * If providing a service's concept ID here, it will uniquely identify those services.

        Parameters:
            IDs (String, List): ID(s) to search by. Can be provided as a string or list of strings.
        """
        super().concept_id(IDs)
        return self

    def keyword(self, text: str) -> Type[CollectionQuery]:
        """Case insentive and wildcard (*) search through over two dozen fields in
        a CMR collection record. This allows for searching against fields like
        summary and science keywords.

        Parameters:
            text (String): text to search for
        """
        super().keyword(text)
        return self

    def doi(self, doi: str) -> Type[CollectionQuery]:
        """Searh datasets by DOI

        ???+ Tip
            Not all datasets have an associated DOI, also DOI search works
            only at the dataset level but not the granule (data) level.
            We need to search by DOI, grab the concept_id and then get the data.

        Parameters:
            doi (String): DOI of a datasets, e.g. 10.5067/AQR50-3Q7CS
        """
        if not isinstance(doi, str):
            raise TypeError("doi must be of type str")

        self.params["doi"] = doi
        return self

    def parameters(self, **kwargs: Any) -> Type[CollectionQuery]:
        """Provide query parameters as keyword arguments. The keyword needs to match the name
        of the method, and the value should either be the value or a tuple of values.

        ???+ Example
            ```python
            query = DataCollections.parameters(short_name="AST_L1T",
                                               temporal=("2015-01","2015-02"),
                                               point=(42.5, -101.25))
            ```
        Returns:
            Query instance
        """
        methods = {}
        for name, func in getmembers(self, predicate=ismethod):
            methods[name] = func

        for key, val in kwargs.items():
            # verify the key matches one of our methods
            if key not in methods:
                raise ValueError("Unknown key {}".format(key))

            # call the method
            if isinstance(val, tuple):
                methods[key](*val)
            else:
                methods[key](val)

        return self

    def print_help(self, method: str = "fields") -> None:
        """Prints the help information for a given method"""
        print("Class components: \n")
        print([method for method in dir(self) if method.startswith("_") is False])
        help(getattr(self, method))

    def fields(self, fields: Optional[List[str]] = None) -> Type[CollectionQuery]:
        """Masks the response by only showing the fields included in this list
        Parameters:
            fields (List): list of fields to show, these fields come from the UMM model e.g. Abstract, Title
        """
        self._fields = fields
        return self

    def debug(self, debug: bool = True) -> Type[CollectionQuery]:
        """If True, prints the actual query to CMR, notice that the pagination happens in the headers.
        Parameters:
            debug (Boolean): Print CMR query.
        """
        self._debug = True
        return self

    def cloud_hosted(self, cloud_hosted: bool = True) -> Type[CollectionQuery]:
        """Only match granules that are hosted in the cloud. This is valid for public collections.

        ???+ Tip
            Cloud hosted collections can be public or restricted.
            Restricted collections will not be matched using this parameter

        Parameters:
            cloud_hosted (Boolean): True to require granules only be online
        """
        if not isinstance(cloud_hosted, bool):
            raise TypeError("cloud_hosted must be of type bool")

        self.params["cloud_hosted"] = cloud_hosted
        if hasattr(self, "DAAC"):
            provider = find_provider(self.DAAC, cloud_hosted)
            self.params["provider"] = provider
        return self

    def provider(self, provider: str = "") -> Type[CollectionQuery]:
        """Only match collections from a given provider, a NASA datacenter or DAAC can have 1 or more providers
        i.e. PODAAC is a data center or DAAC, PODAAC is the default provider for on prem data, POCLOUD is
        the PODAAC provider for their data in the cloud.

        Parameters:
            provider (String): a provider code for any DAAC. e.g. POCLOUD, NSIDC_CPRD, etc.
        """
        self.params["provider"] = provider
        return self

    def data_center(self, data_center_name: str = "") -> Type[CollectionQuery]:
        """An alias name for `daac()`
        Parameters:
            data_center_name (String): DAAC shortname, e.g. NSIDC, PODAAC, GESDISC
        """
        return self.daac(data_center_name)

    def daac(self, daac_short_name: str = "") -> Type[CollectionQuery]:
        """Only match collections for a given DAAC, by default the on-prem collections for the DAAC
        Parameters:
            daac_short_name (String): a DAAC shortname, e.g. NSIDC, PODAAC, GESDISC
        """
        if "cloud_hosted" in self.params:
            cloud_hosted = self.params["cloud_hosted"]
        else:
            cloud_hosted = False
        self.DAAC = daac_short_name
        self.params["provider"] = find_provider(daac_short_name, cloud_hosted)
        return self

    def get(self, limit: int = 2000) -> list:
        """Get all the collections (datasets) that match with our current parameters
        up to some limit, even if spanning multiple pages.

        ???+ Tip
            The default page size is 2000, we need to be careful with the request size because all the JSON
            elements will be loaded into memory. This is more of an issue with granules than collections as
            they can be potentially millions of them.

        Parameters:
            limit (Integer): The number of results to return
        Returns:
            query results as a list of `DataCollection` instances.
        """

        page_size = min(limit, 2000)
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
        """Filter by an open or closed date range. Dates can be provided as datetime objects
        or ISO 8601 formatted strings. Multiple ranges can be provided by successive calls.
        to this method before calling execute().

        Parameters:
            date_from (String): earliest date of temporal range
            date_to (string): latest date of temporal range
            exclude_boundary (Boolean): whether or not to exclude the date_from/to in the matched range
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
    A Granule oriented client for NASA CMR

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
        """Base class for Granule and Collection CMR queries."""
        super().__init__(*args, **kwargs)
        self.session = session()
        if auth is not None and auth.authenticated:
            # To search we need the new bearer tokens from NASA Earthdata
            self.session = auth.get_session(bearer_token=True)

        self._debug = False

    def hits(self) -> int:
        """
        Returns the number of hits the current query will return. This is done by
        making a lightweight query to CMR and inspecting the returned headers.

        :returns: number of results reported by CMR
        """

        url = self._build_url()

        response = self.session.get(url, headers=self.headers, params={"page_size": 0})

        try:
            response.raise_for_status()
        except exceptions.HTTPError as ex:
            raise RuntimeError(ex.response.text)

        return int(response.headers["CMR-Hits"])

    def parameters(self, **kwargs: Any) -> Type[CollectionQuery]:
        """Provide query parameters as keyword arguments. The keyword needs to match the name
        of the method, and the value should either be the value or a tuple of values.

        ???+ Example
            ```python
            query = DataCollections.parameters(short_name="AST_L1T",
                                               temporal=("2015-01","2015-02"),
                                               point=(42.5, -101.25))
            ```
        Returns:
            Query instance
        """
        methods = {}
        for name, func in getmembers(self, predicate=ismethod):
            methods[name] = func

        for key, val in kwargs.items():
            # verify the key matches one of our methods
            if key not in methods:
                raise ValueError("Unknown key {}".format(key))

            # call the method
            if isinstance(val, tuple):
                methods[key](*val)
            else:
                methods[key](val)

        return self

    def provider(self, provider: str = "") -> Type[CollectionQuery]:
        """Only match collections from a given provider, a NASA datacenter or DAAC can have 1 or more providers
        i.e. PODAAC is a data center or DAAC, PODAAC is the default provider for on prem data, POCLOUD is
        the PODAAC provider for their data in the cloud.

        Parameters:
            provider (String): a provider code for any DAAC. e.g. POCLOUD, NSIDC_CPRD, etc.
        """
        self.params["provider"] = provider
        return self

    def data_center(self, data_center_name: str = "") -> Type[CollectionQuery]:
        """An alias name for `daac()`
        Parameters:
            data_center_name (String): DAAC shortname, e.g. NSIDC, PODAAC, GESDISC
        """
        return self.daac(data_center_name)

    def daac(self, daac_short_name: str = "") -> Type[CollectionQuery]:
        """Only match collections for a given DAAC, by default the on-prem collections for the DAAC
        Parameters:
            daac_short_name (String): a DAAC shortname, e.g. NSIDC, PODAAC, GESDISC
        """
        if "cloud_hosted" in self.params:
            cloud_hosted = self.params["cloud_hosted"]
        else:
            cloud_hosted = False
        self.DAAC = daac_short_name
        self.params["provider"] = find_provider(daac_short_name, cloud_hosted)
        return self

    def orbit_number(self, orbit1: int, orbit2: int) -> Type[GranuleQuery]:
        """Filter by the orbit number the granule was acquired during. Either a single
        orbit can be targeted or a range of orbits.

        Parameter:
            orbit1: orbit to target (lower limit of range when orbit2 is provided)
            orbit2: upper limit of range
        """
        super().orbit_number(orbit1, orbit2)
        return self

    def cloud_hosted(self, cloud_hosted: bool = True) -> Type[CollectionQuery]:
        """Only match granules that are hosted in the cloud. This is valid for public
        collections and if we are using the short_name parameter. Concept-Id is unambiguous.

        ???+ Tip
            Cloud hosted collections can be public or restricted.
            Restricted collections will not be matched using this parameter

        Parameters:
            cloud_hosted (Boolean): True to require granules only be online
        """
        if not isinstance(cloud_hosted, bool):
            raise TypeError("cloud_hosted must be of type bool")

        if "short_name" in self.params:
            provider = find_provider_by_shortname(
                self.params["short_name"], cloud_hosted
            )
            if provider is not None:
                self.params["provider"] = provider
        return self

    def granule_name(self, granule_name: str) -> Type[CollectionQuery]:
        """Find granules matching either granule ur or producer granule id,
        queries using the readable_granule_name metadata field.

        ???+ Tip
            We can use wirldcards on a granule name to further refine our search
            i.e. MODGRNLD.*.daily.*

        Parameters:
            granule_name (String): granule name (accepts wildcards)
        """
        if not isinstance(granule_name, str):
            raise TypeError("granule_name must be of type string")

        self.params["readable_granule_name"] = granule_name
        self.params["options[readable_granule_name][pattern]"] = True
        return self

    def online_only(self, online_only: bool = True) -> Type[GranuleQuery]:
        """Only match granules that are listed online and not available for download.
        The opposite of this method is downloadable().
        Parameters:
            online_only (Boolean): True to require granules only be online
        """
        super().online_only(online_only)
        return self

    def day_night_flag(self, day_night_flag: str) -> Type[GranuleQuery]:
        """Filter by period of the day the granule was collected during.

        Parameters:
            day_night_flag: "day", "night", or "unspecified"
        """
        super().day_night_flag(day_night_flag)
        return self

    def instrument(self, instrument: str = "") -> Type[GranuleQuery]:
        """Filter by the instrument associated with the granule.

        Parameters:
            instrument (str): name of the instrument
        """
        super().instrument(instrument)
        return self

    def platform(self, platform: str = "") -> Type[GranuleQuery]:
        """Filter by the satellite platform the granule came from.

        Parameters:
            platform: name of the satellite
        """
        super().platform(platform)
        return self

    def cloud_cover(
        self, min_cover: int = 0, max_cover: int = 100
    ) -> Type[GranuleQuery]:
        """Filter by the percentage of cloud cover present in the granule.

        Parameters:
            min_cover (int): minimum percentage of cloud cover
            max_cover (int): maximum percentage of cloud cover
        """
        super().cloud_cover(min_cover, max_cover)
        return self

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
        """Check if a granule record in CMR advertises "direct access"."""
        if "RelatedUrls" not in granule["umm"]:
            return False

        direct_def = "GET DATA VIA DIRECT ACCESS"
        for link in granule["umm"]["RelatedUrls"]:
            if "protected" in link["URL"] or link["Type"] == direct_def:
                return True
        return False

    def short_name(self, short_name: str = "") -> Type[GranuleQuery]:
        """
        Filter by short name (aka product or collection name).
        :param short_name: name of collection
        :returns: Query instance
        """
        super().short_name(short_name)
        return self

    def get(self, limit: int = 2000) -> list:
        """Get all the collections (datasets) that match with our current parameters
        up to some limit, even if spanning multiple pages.

        ???+ Tip
            The default page size is 2000, we need to be careful with the request size because all the JSON
            elements will be loaded into memory. This is more of an issue with granules than collections as
            they can be potentially millions of them.

        Parameters:
            limit (Integer): The number of results to return
        Returns:
            query results as a list of `DataCollection` instances.
        """
        # TODO: implement items() iterator
        page_size = min(limit, 2000)
        url = self._build_url()

        results: List = []
        page = 1
        headers: Dict[str, str] = {}
        while len(results) < limit:
            params = {"page_size": page_size}
            # TODO: should be in a logger
            if self._debug:
                print(f"Fetching: {url}", f"headers: {headers}")

            response = self.session.get(url, params=params, headers=headers)

            try:
                response.raise_for_status()
            except exceptions.HTTPError as ex:
                raise RuntimeError(ex.response.text)

            if self._format == "json":
                latest = response.json()["feed"]["entry"]
            elif self._format == "umm_json":
                json_response = response.json()["items"]
                if len(json_response) > 0:
                    if "CMR-Search-After" in response.headers:
                        headers["CMR-Search-After"] = response.headers[
                            "CMR-Search-After"
                        ]
                    else:
                        headers = {}
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
        """If True, prints the actual query to CMR, notice that the pagination happens in the headers.
        Parameters:
            debug (Boolean): Print CMR query.
        """
        self._debug = True
        return self

    def temporal(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        exclude_boundary: bool = False,
    ) -> Type[GranuleQuery]:
        """Filter by an open or closed date range.
        Dates can be provided as a datetime objects or ISO 8601 formatted strings. Multiple
        ranges can be provided by successive calls to this method before calling execute().

        Parameters:
            date_from (Date, String): earliest date of temporal range
            date_to (Date, String): latest date of temporal range
            exclude_boundary (Boolean): whether or not to exclude the date_from/to in the matched range
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

    def version(self, version: str = "") -> Type[GranuleQuery]:
        """Filter by version. Note that CMR defines this as a string. For example,
        MODIS version 6 products must be searched for with "006".

        Parameters:
            version: version string
        """
        super().version(version)
        return self

    def point(self, lon: str, lat: str) -> Type[GranuleQuery]:
        """Filter by granules that include a geographic point.

        Parameters:
            lon (String): longitude of geographic point
            lat (String): latitude of geographic point
        """
        super().point(lon, lat)
        return self

    def polygon(self, coordinates: List[Tuple[str, str]]) -> Type[GranuleQuery]:
        """Filter by granules that overlap a polygonal area. Must be used in combination with a
        collection filtering parameter such as short_name or entry_title.

        Parameters:
            coordinates (List): list of (lon, lat) tuples
        """
        super().polygon(coordinates)
        return self

    def bounding_box(
        self,
        lower_left_lon: str,
        lower_left_lat: str,
        upper_right_lon: str,
        upper_right_lat: str,
    ) -> Type[GranuleQuery]:
        """Filter by granules that overlap a bounding box. Must be used in combination with
        a collection filtering parameter such as short_name or entry_title.

        Parameters:
            lower_left_lon: lower left longitude of the box
            lower_left_lat: lower left latitude of the box
            upper_right_lon: upper right longitude of the box
            upper_right_lat: upper right latitude of the box
        """
        super().bounding_box(
            lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat
        )
        return self

    def line(self, coordinates: List[Tuple[str, str]]) -> Type[GranuleQuery]:
        """Filter by granules that overlap a series of connected points. Must be used in combination
        with a collection filtering parameter such as short_name or entry_title.

        Parameters:
            coordinates (List): a list of (lon, lat) tuples
        """
        super().line(coordinates)
        return self

    def downloadable(self, downloadable: bool = True) -> Type[GranuleQuery]:
        """Only match granules that are available for download. The opposite of this
        method is online_only().

        Parameters:
            downloadable: True to require granules be downloadable
        """
        super().downloadable(downloadable)
        return self

    def doi(self, doi: str) -> Type[GranuleQuery]:
        """Searh data granules by DOI

        ???+ Tip
            Not all datasets have an associated DOI, internally if a DOI is found
            earthaccess will grab the concept_id for the query to CMR.

        Parameters:
            doi (String): DOI of a datasets, e.g. 10.5067/AQR50-3Q7CS
        """
        collection = DataCollections().doi(doi).get()
        if len(collection) > 0:
            concept_id = collection[0].concept_id()
            self.params["concept_id"] = concept_id
        else:
            print(
                f"earthaccess couldn't find any associated collections with the DOI: {doi}"
            )
        return self
