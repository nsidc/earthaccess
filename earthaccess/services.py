from typing import Any, List, Optional

from cmr import ServiceQuery
from requests import exceptions, session

from .auth import Auth

class DataService(ServiceQuery):
    """A Service client for NASA CMR that returns data on collection services.
    
    API: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#service
    """
    
    _format = "umm_json"
    
    def __init__(self, auth: Optional[Auth] = None, *args: Any, **kwargs: Any) -> None:
        """Build an instance of DataServics to query CMR.

        Parameters:
            auth (Optional[Auth], optional): An authenticated `Auth` instance. 
            This is an optional parameter for queries that need authentication, 
            e.g. restricted datasets.
        """
        
        super().__init__(*args, **kwargs)
        self._debug = False
        self.session = session()
        if auth is not None and auth.authenticated:
            # To search, we need the new bearer tokens from NASA Earthdata
            self.session = auth.get_session(bearer_token=True)
            
    def get(self, limit=2000) -> List:
        """Get all service reuslts up to some limit.

        Parameters
            limit (int): The number of results to return
        
        Returns
            Query results as a list
        """
        
        page_size = min(limit, 2000)
        url = self._build_url()

        results = []
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
                latest = response.json()['items']
            else:
                latest = [response.text]

            if len(latest) == 0:
                break

            results.extend(latest)
            page += 1

        return results