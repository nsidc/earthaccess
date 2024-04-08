import datetime as dt
from inspect import getmembers, ismethod

import dateutil.parser as parser
import requests
from cmr import CollectionQuery, GranuleQuery

from .auth import Auth
from .daac import find_provider, find_provider_by_shortname
from .results import DataCollection, DataGranule
from .typing_ import (
    Any,
    Dict,
    List,
    Never,
    Optional,
    Self,
    Sequence,
    SupportsFloat,
    Tuple,
    TypeAlias,
    Union,
    override,
)

FloatLike: TypeAlias = Union[str, SupportsFloat]
PointLike: TypeAlias = Tuple[FloatLike, FloatLike]


def get_results(
    query: Union[CollectionQuery, GranuleQuery], limit: int = 2000
) -> List[Any]:
    """
    Get all results up to some limit, even if spanning multiple pages.

    ???+ Tip
        The default page size is 2000, if the supplied value is greater then the Search-After header
        will be used to iterate across multiple requests until either the limit has been reached
        or there are no more results.
    Parameters:
        limit: The number of results to return

    Returns:
        query results as a list
    """

    page_size = min(limit, 2000)
    url = query._build_url()

    results: List[Any] = []
    more_results = True
    headers = dict(query.headers or {})

    while more_results:
        response = requests.get(url, headers=headers, params={"page_size": page_size})

        if cmr_search_after := query.headers.get("cmr-search-after"):
            headers["cmr-search-after"] = cmr_search_after

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            raise RuntimeError(ex.response.text) from ex

        latest = response.json()["items"]

        results.extend(latest)

        more_results = page_size <= len(latest) and len(results) < limit

    return results


class DataCollections(CollectionQuery):
    """
    ???+ Info
        The DataCollection class queries against https://cmr.earthdata.nasa.gov/search/collections.umm_json,
        the response has to be in umm_json to use the result classes.
    """

    _fields: Optional[List[str]] = None
    _format = "umm_json"

    def __init__(self, auth: Optional[Auth] = None, *args: Any, **kwargs: Any) -> None:
        """Builds an instance of DataCollections to query CMR

        Parameters:
            auth: An authenticated `Auth` instance. This is an optional parameter
                for queries that need authentication, e.g. restricted datasets.
        """
        super().__init__(*args, **kwargs)

        self.session = (
            # To search, we need the new bearer tokens from NASA Earthdata
            auth.get_session(bearer_token=True)
            if auth is not None and auth.authenticated
            else requests.session()
        )

        self._debug = False

        self.params["has_granules"] = True
        self.params["include_granule_counts"] = True

    @override
    def hits(self) -> Union[int, Never]:
        """Returns the number of hits the current query will return. This is done by
        making a lightweight query to CMR and inspecting the returned headers.
        Restricted datasets will always return zero results even if there are results.

        Raises:
            RuntimeError: if the CMR query fails

        Returns:
            The number of results reported by CMR.
        """
        url = self._build_url()

        response = self.session.get(url, headers=self.headers, params={"page_size": 0})

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            raise RuntimeError(ex.response.text) from ex

        return int(response.headers["CMR-Hits"])

    @override
    def get(self, limit: int = 2000) -> Union[List[DataCollection], Never]:
        """Get all the collections (datasets) that match with our current parameters
        up to some limit, even if spanning multiple pages.

        ???+ Tip
            The default page size is 2000, we need to be careful with the request size because all the JSON
            elements will be loaded into memory. This is more of an issue with granules than collections as
            they can be potentially millions of them.

        Parameters:
            limit: The number of results to return

        Raises:
            RuntimeError: if the CMR query fails

        Returns:
            query results as a (possibly empty) list of `DataCollection` instances.
        """

        return [
            DataCollection(collection, self._fields)
            for collection in get_results(self, limit)
        ]

    @override
    def concept_id(self, IDs: Sequence[str]) -> Union[Self, Never]:
        """Filter by concept ID.
        For example: C1299783579-LPDAAC_ECS or G1327299284-LPDAAC_ECS, S12345678-LPDAAC_ECS

        Collections, granules, tools, services are uniquely identified with this ID.
        >
        * If providing a collection's concept ID here, it will filter by granules associated with that collection.
        * If providing a granule's concept ID here, it will uniquely identify those granules.
        * If providing a tool's concept ID here, it will uniquely identify those tools.
        * If providing a service's concept ID here, it will uniquely identify those services.

        Parameters:
            IDs: ID(s) to search by. Can be provided as a string or list of strings.

        Raises:
            ValueError: if an ID does not start with a valid prefix

        Returns:
            self
        """
        return super().concept_id(IDs)

    @override
    def keyword(self, text: str) -> Self:
        """Case-insensitive and wildcard (*) search through over two dozen fields in
        a CMR collection record. This allows for searching against fields like
        summary and science keywords.

        Parameters:
            text: text to search for

        Returns:
            self
        """
        return super().keyword(text)

    def doi(self, doi: str) -> Union[Self, Never]:
        """Search datasets by DOI.

        ???+ Tip
            Not all datasets have an associated DOI, also DOI search works
            only at the dataset level but not the granule (data) level.
            We need to search by DOI, grab the concept_id and then get the data.

        Parameters:
            doi: DOI of a datasets, e.g. 10.5067/AQR50-3Q7CS

        Raises:
            TypeError: if `doi` is not of type `str`

        Returns:
            self
        """
        if not isinstance(doi, str):
            raise TypeError("doi must be of type str")

        self.params["doi"] = doi
        return self

    def instrument(self, instrument: str) -> Union[Self, Never]:
        """Searh datasets by instrument

        ???+ Tip
            Not all datasets have an associated instrument. This works
            only at the dataset level but not the granule (data) level.

        Parameters:
            instrument (String): instrument of a datasets, e.g. instrument=GEDI

        Raises:
            TypeError: if `instrument` is not of type `str`

        Returns:
            self
        """
        if not isinstance(instrument, str):
            raise TypeError("instrument must be of type str")

        self.params["instrument"] = instrument
        return self

    def project(self, project: str) -> Union[Self, Never]:
        """Searh datasets by associated project

        ???+ Tip
            Not all datasets have an associated project. This works
            only at the dataset level but not the granule (data) level.
            Will return datasets across DAACs matching the project.

        Parameters:
            project (String): associated project of a datasets, e.g. project=EMIT

        Raises:
            TypeError: if `project` is not of type `str`

        Returns:
            self
        """
        if not isinstance(project, str):
            raise TypeError("project must be of type str")

        self.params["project"] = project
        return self

    @override
    def parameters(self, **kwargs: Any) -> Union[Self, Never]:
        """Provide query parameters as keyword arguments. The keyword needs to match the name
        of the method, and the value should either be the value or a tuple of values.

        ???+ Example
            ```python
            query = DataCollections.parameters(short_name="AST_L1T",
                                               temporal=("2015-01","2015-02"),
                                               point=(42.5, -101.25))
            ```

        Raises:
            ValueError: if the name of a keyword argument is not the name of a method
            TypeError: if the value of a keyword argument is not an argument or tuple
                of arguments matching the number and type(s) of the method's parameters

        Returns:
            self
        """
        methods = dict(getmembers(self, predicate=ismethod))

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
        """Prints the help information for a given method."""
        print("Class components: \n")
        print([method for method in dir(self) if method.startswith("_") is False])
        help(getattr(self, method))

    def fields(self, fields: Optional[List[str]] = None) -> Self:
        """Masks the response by only showing the fields included in this list.

        Parameters:
            fields (List): list of fields to show, these fields come from the UMM model e.g. Abstract, Title

        Returns:
            self
        """
        self._fields = fields
        return self

    def debug(self, debug: bool = True) -> Self:
        """If True, prints the actual query to CMR, notice that the pagination happens in the headers.

        Parameters:
            debug (Boolean): Print CMR query.

        Returns:
            self
        """
        self._debug = debug
        return self

    def cloud_hosted(self, cloud_hosted: bool = True) -> Union[Self, Never]:
        """Only match granules that are hosted in the cloud. This is valid for public collections.

        ???+ Tip
            Cloud hosted collections can be public or restricted.
            Restricted collections will not be matched using this parameter

        Parameters:
            cloud_hosted: True to require granules only be online

        Raises:
            TypeError: if `cloud_hosted` is not of type `bool`

        Returns:
            self
        """
        if not isinstance(cloud_hosted, bool):
            raise TypeError("cloud_hosted must be of type bool")

        self.params["cloud_hosted"] = cloud_hosted
        if hasattr(self, "DAAC"):
            provider = find_provider(self.DAAC, cloud_hosted)
            self.params["provider"] = provider
        return self

    @override
    def provider(self, provider: str) -> Self:
        """Only match collections from a given provider.

        A NASA datacenter or DAAC can have one or more providers.
        E.g., PODAAC is a data center or DAAC; PODAAC is the default provider for on-premises data,
        POCLOUD is the PODAAC provider for their data in the cloud.

        Parameters:
            provider: a provider code for any DAAC, e.g. POCLOUD, NSIDC_CPRD, etc.

        Returns:
            self
        """
        self.params["provider"] = provider
        return self

    def data_center(self, data_center_name: str) -> Self:
        """An alias name for the `daac` method.

        Parameters:
            data_center_name: DAAC shortname, e.g. NSIDC, PODAAC, GESDISC

        Returns:
            self
        """
        return self.daac(data_center_name)

    def daac(self, daac_short_name: str) -> Self:
        """Only match collections for a given DAAC, by default the on-prem collections for the DAAC.

        Parameters:
            daac_short_name: a DAAC shortname, e.g. NSIDC, PODAAC, GESDISC

        Returns:
            self
        """
        if "cloud_hosted" in self.params:
            cloud_hosted = self.params["cloud_hosted"]
        else:
            cloud_hosted = False
        self.DAAC = daac_short_name
        self.params["provider"] = find_provider(daac_short_name, cloud_hosted)
        return self

    @override
    def temporal(
        self,
        date_from: Optional[Union[str, dt.datetime]] = None,
        date_to: Optional[Union[str, dt.datetime]] = None,
        exclude_boundary: bool = False,
    ) -> Union[Self, Never]:
        """Filter by an open or closed date range. Dates can be provided as datetime objects
        or ISO 8601 formatted strings. Multiple ranges can be provided by successive calls
        to this method before calling execute().

        Parameters:
            date_from (String or Datetime object): earliest date of temporal range
            date_to (String or Datetime object): latest date of temporal range
            exclude_boundary (Boolean): whether or not to exclude the date_from/to in the matched range.

        Raises:
            ValueError: if `date_from` or `date_to` is a non-`None` value that is
                neither a datetime object nor a string that can be parsed as a datetime
                object; or if `date_from` and `date_to` are both datetime objects (or
                parsable as such) and `date_from` is greater than `date_to`

        Returns:
            self
        """
        DEFAULT = dt.datetime(1979, 1, 1)
        if date_from is not None and not isinstance(date_from, dt.datetime):
            try:
                date_from = parser.parse(date_from, default=DEFAULT).isoformat() + "Z"
            except Exception:
                print("The provided start date was not recognized")
                date_from = ""

        if date_to is not None and not isinstance(date_to, dt.datetime):
            try:
                date_to = parser.parse(date_to, default=DEFAULT).isoformat() + "Z"
            except Exception:
                print("The provided end date was not recognized")
                date_to = ""

        return super().temporal(date_from, date_to, exclude_boundary)


class DataGranules(GranuleQuery):
    """A Granule oriented client for NASA CMR.

    API: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
    """

    _format = "umm_json"

    def __init__(self, auth: Optional[Auth] = None, *args: Any, **kwargs: Any) -> None:
        """Base class for Granule and Collection CMR queries."""
        super().__init__(*args, **kwargs)

        self.session = (
            # To search, we need the new bearer tokens from NASA Earthdata
            auth.get_session(bearer_token=True)
            if auth is not None and auth.authenticated
            else requests.session()
        )

        self._debug = False

    @override
    def hits(self) -> Union[int, Never]:
        """Returns the number of hits the current query will return.
        This is done by making a lightweight query to CMR and inspecting the returned headers.

        Raises:
            RuntimeError: if the CMR query fails

        Returns:
            The number of results reported by CMR.
        """

        url = self._build_url()

        response = self.session.get(url, headers=self.headers, params={"page_size": 0})

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            if ex.response is not None:
                raise RuntimeError(ex.response.text) from ex
            else:
                raise RuntimeError(str(ex)) from ex

        return int(response.headers["CMR-Hits"])

    @override
    def get(self, limit: int = 2000) -> Union[List[DataGranule], Never]:
        """Get all the collections (datasets) that match with our current parameters
        up to some limit, even if spanning multiple pages.

        ???+ Tip
            The default page size is 2000, we need to be careful with the request size because all the JSON
            elements will be loaded into memory. This is more of an issue with granules than collections as
            they can be potentially millions of them.

        Parameters:
            limit: The number of results to return

        Raises:
            RuntimeError: if the CMR query fails

        Returns:
            query results as a (possibly empty) list of `DataGranules` instances.
        """
        response = get_results(self, limit)

        cloud = self._is_cloud_hosted(response[0])

        return [DataGranule(granule, cloud_hosted=cloud) for granule in response]

    @override
    def parameters(self, **kwargs: Any) -> Union[Self, Never]:
        """Provide query parameters as keyword arguments. The keyword needs to match the name
        of the method, and the value should either be the value or a tuple of values.

        ???+ Example
            ```python
            query = DataCollections.parameters(short_name="AST_L1T",
                                               temporal=("2015-01","2015-02"),
                                               point=(42.5, -101.25))
            ```

        Raises:
            ValueError: if the name of a keyword argument is not the name of a method
            TypeError: if the value of a keyword argument is not an argument or tuple
                of arguments matching the number and type(s) of the method's parameters

        Returns:
            self
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

    @override
    def provider(self, provider: str) -> Self:
        """Only match collections from a given provider.
        A NASA datacenter or DAAC can have one or more providers.
        For example, PODAAC is a data center or DAAC,
        PODAAC is the default provider for on-prem data, and POCLOUD is
        the PODAAC provider for their data in the cloud.

        Parameters:
            provider: a provider code for any DAAC, e.g. POCLOUD, NSIDC_CPRD, etc.

        Returns:
            self
        """
        self.params["provider"] = provider
        return self

    def data_center(self, data_center_name: str) -> Self:
        """An alias name for `daac()`.

        Parameters:
            data_center_name (String): DAAC shortname, e.g. NSIDC, PODAAC, GESDISC

        Returns:
            self
        """
        return self.daac(data_center_name)

    def daac(self, daac_short_name: str) -> Self:
        """Only match collections for a given DAAC. Default to on-prem collections for the DAAC.

        Parameters:
            daac_short_name: a DAAC shortname, e.g. NSIDC, PODAAC, GESDISC

        Returns:
            self
        """
        if "cloud_hosted" in self.params:
            cloud_hosted = self.params["cloud_hosted"]
        else:
            cloud_hosted = False
        self.DAAC = daac_short_name
        self.params["provider"] = find_provider(daac_short_name, cloud_hosted)
        return self

    @override
    def orbit_number(
        self,
        orbit1: FloatLike,
        orbit2: Optional[FloatLike] = None,
    ) -> Self:
        """Filter by the orbit number the granule was acquired during. Either a single
        orbit can be targeted or a range of orbits.

        Parameter:
            orbit1: orbit to target (lower limit of range when orbit2 is provided)
            orbit2: upper limit of range

        Returns:
            self
        """
        return super().orbit_number(orbit1, orbit2)

    def cloud_hosted(self, cloud_hosted: bool = True) -> Union[Self, Never]:
        """Only match granules that are hosted in the cloud.
        This is valid for public collections and when using the short_name parameter.
        Concept-Id is unambiguous.

        ???+ Tip
            Cloud-hosted collections can be public or restricted.
            Restricted collections will not be matched using this parameter.

        Parameters:
            cloud_hosted: True to require granules only be online

        Raises:
            TypeError: if `cloud_hosted` is not of type `bool`

        Returns:
            self
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

    def granule_name(self, granule_name: str) -> Union[Self, Never]:
        """Find granules matching either granule ur or producer granule id,
        queries using the readable_granule_name metadata field.

        ???+ Tip
            We can use wildcards on a granule name to further refine our search,
            e.g. `MODGRNLD.*.daily.*`.

        Parameters:
            granule_name: granule name (accepts wildcards)

        Raises:
            TypeError: if `granule_name` is not of type `str`

        Returns:
            self
        """
        if not isinstance(granule_name, str):
            raise TypeError("granule_name must be of type string")

        self.params["readable_granule_name"] = granule_name
        self.params["options[readable_granule_name][pattern]"] = True
        return self

    @override
    def online_only(self, online_only: bool = True) -> Union[Self, Never]:
        """Only match granules that are listed online and not available for download.
        The opposite of this method is downloadable().

        Parameters:
            online_only: True to require granules only be online

        Raises:
            TypeError: if `online_only` is not of type `bool`

        Returns:
            self
        """
        return super().online_only(online_only)

    @override
    def day_night_flag(self, day_night_flag: str) -> Union[Self, Never]:
        """Filter by period of the day the granule was collected during.

        Parameters:
            day_night_flag: "day", "night", or "unspecified"

        Raises:
            TypeError: if `day_night_flag` is not of type `str`
            ValueError: if `day_night_flag` is not one of `"day"`, `"night"`, or
                `"unspecified"`

        Returns:
            self
        """
        return super().day_night_flag(day_night_flag)

    @override
    def instrument(self, instrument: str) -> Union[Self, Never]:
        """Filter by the instrument associated with the granule.

        Parameters:
            instrument: name of the instrument

        Raises:
            ValueError: if `instrument` is not a non-empty string

        Returns:
            self
        """
        return super().instrument(instrument)

    @override
    def platform(self, platform: str) -> Union[Self, Never]:
        """Filter by the satellite platform the granule came from.

        Parameters:
            platform: name of the satellite

        Raises:
            ValueError: if `platform` is not a non-empty string

        Returns:
            self
        """
        return super().platform(platform)

    @override
    def cloud_cover(
        self,
        min_cover: Optional[FloatLike] = 0,
        max_cover: Optional[FloatLike] = 100,
    ) -> Union[Self, Never]:
        """Filter by the percentage of cloud cover present in the granule.

        Parameters:
            min_cover: minimum percentage of cloud cover
            max_cover: maximum percentage of cloud cover

        Raises:
            ValueError: if `min_cover` or `max_cover` is not convertible to a float,
                or if `min_cover` is greater than `max_cover`

        Returns:
            self
        """
        return super().cloud_cover(min_cover, max_cover)

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

    @override
    def short_name(self, short_name: str) -> Self:
        """Filter by short name (aka product or collection name).

        Parameters:
            short_name: name of a collection

        Returns:
            self
        """
        return super().short_name(short_name)

    def debug(self, debug: bool = True) -> Self:
        """If True, prints the actual query to CMR, notice that the pagination happens in the headers.

        Parameters:
            debug: Print CMR query.

        Returns:
            self
        """
        self._debug = debug
        return self

    @override
    def temporal(
        self,
        date_from: Optional[Union[str, dt.datetime]] = None,
        date_to: Optional[Union[str, dt.datetime]] = None,
        exclude_boundary: bool = False,
    ) -> Union[Self, Never]:
        """Filter by an open or closed date range.
        Dates can be provided as a datetime objects or ISO 8601 formatted strings. Multiple
        ranges can be provided by successive calls to this method before calling execute().

        Parameters:
            date_from: earliest date of temporal range
            date_to: latest date of temporal range
            exclude_boundary: whether to exclude the date_from/to in the matched range

        Raises:
            ValueError: if `date_from` or `date_to` is a non-`None` value that is
                neither a datetime object nor a string that can be parsed as a datetime
                object; or if `date_from` and `date_to` are both datetime objects (or
                parsable as such) and `date_from` is greater than `date_to`

        Returns:
            self
        """
        DEFAULT = dt.datetime(1979, 1, 1)
        if date_from is not None and not isinstance(date_from, dt.datetime):
            try:
                date_from = parser.parse(date_from, default=DEFAULT).isoformat() + "Z"
            except Exception:
                print("The provided start date was not recognized")
                date_from = ""

        if date_to is not None and not isinstance(date_to, dt.datetime):
            try:
                date_to = parser.parse(date_to, default=DEFAULT).isoformat() + "Z"
            except Exception:
                print("The provided end date was not recognized")
                date_to = ""

        return super().temporal(date_from, date_to, exclude_boundary)

    @override
    def version(self, version: str) -> Self:
        """Filter by version. Note that CMR defines this as a string. For example,
        MODIS version 6 products must be searched for with "006".

        Parameters:
            version: version string

        Returns:
            self
        """
        return super().version(version)

    @override
    def point(self, lon: FloatLike, lat: FloatLike) -> Union[Self, Never]:
        """Filter by granules that include a geographic point.

        Parameters:
            lon (String): longitude of geographic point
            lat (String): latitude of geographic point

        Raises:
            ValueError: if `lon` or `lat` cannot be converted to a float

        Returns:
            self
        """
        return super().point(lon, lat)

    @override
    def polygon(self, coordinates: Sequence[PointLike]) -> Union[Self, Never]:
        """Filter by granules that overlap a polygonal area. Must be used in combination with a
        collection filtering parameter such as short_name or entry_title.

        Parameters:
            coordinates: list of (lon, lat) tuples

        Raises:
            ValueError: if `coordinates` is not a sequence of at least 4 coordinate
            pairs, any of the coordinates cannot be converted to a float, or the first
            and last coordinate pairs are not equal

        Returns:
            self
        """
        return super().polygon(coordinates)

    @override
    def bounding_box(
        self,
        lower_left_lon: FloatLike,
        lower_left_lat: FloatLike,
        upper_right_lon: FloatLike,
        upper_right_lat: FloatLike,
    ) -> Union[Self, Never]:
        """Filter by granules that overlap a bounding box. Must be used in combination with
        a collection filtering parameter such as short_name or entry_title.

        Parameters:
            lower_left_lon: lower left longitude of the box
            lower_left_lat: lower left latitude of the box
            upper_right_lon: upper right longitude of the box
            upper_right_lat: upper right latitude of the box

        Raises:
            ValueError: if any of the coordinates cannot be converted to a float

        Returns:
            self
        """
        return super().bounding_box(
            lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat
        )

    @override
    def line(self, coordinates: Sequence[PointLike]) -> Union[Self, Never]:
        """Filter by granules that overlap a series of connected points. Must be used in combination
        with a collection filtering parameter such as short_name or entry_title.

        Parameters:
            coordinates: a list of (lon, lat) tuples

        Raises:
            ValueError: if `coordinates` is not a sequence of at least 2 coordinate
            pairs, or any of the coordinates cannot be converted to a float

        Returns:
            self
        """
        return super().line(coordinates)

    @override
    def downloadable(self, downloadable: bool = True) -> Union[Self, Never]:
        """Only match granules that are available for download. The opposite of this
        method is online_only().

        Parameters:
            downloadable: True to require granules be downloadable

        Raises:
            TypeError: if `downloadable` is not of type `bool`

        Returns:
            self
        """
        return super().downloadable(downloadable)

    def doi(self, doi: str) -> Union[Self, Never]:
        """Search data granules by DOI

        ???+ Tip
            Not all datasets have an associated DOI, internally if a DOI is found
            earthaccess will grab the concept_id for the query to CMR.

        Parameters:
            doi: DOI of a dataset, e.g. 10.5067/AQR50-3Q7CS

        Raises:
            RuntimeError: if the CMR query to get the collection for the DOI fails

        Returns:
            self
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
