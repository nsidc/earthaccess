from typing import Any, List, Optional

import requests

from cmr import ServiceQuery

from .auth import Auth
from .utils import _search as search


class DataServices(ServiceQuery):
    """A Service client for NASA CMR that returns data on collection services.

    API: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#service
    """

    _format = "umm_json"

    def __init__(self, auth: Optional[Auth] = None, *args: Any, **kwargs: Any) -> None:
        """Build an instance of DataService to query CMR.

        auth is an optional parameter for queries that need authentication,
        e.g. restricted datasets.

        Parameters:
            auth: An authenticated `Auth` instance.
        """
        super().__init__(*args, **kwargs)
        self._debug = False

        self.session = (
            auth.get_session()
            if auth is not None and auth.authenticated
            else requests.sessions.Session()
        )

    def get(self, limit: int = 2000) -> List:
        """Get all service results up to some limit.

        Parameters
            limit (int): The number of results to return

        Returns:
            Query results as a list
        """
        return search.get_results(self.session, self, limit)
