import requests
from typing_extensions import Any, List, Union

from cmr import CollectionQuery, GranuleQuery, ServiceQuery


def get_results(
    session: requests.Session,
    query: Union[CollectionQuery, GranuleQuery, ServiceQuery],
    limit: int = 2000,
) -> List[Any]:
    """Get all results up to some limit, even if spanning multiple pages.

    ???+ Tip
        The default page size is 2000, if the supplied value is greater then the
        Search-After header will be used to iterate across multiple requests until
        either the limit has been reached or there are no more results.

    Parameters:
        limit: The number of results to return

    Returns:
        query results as a list

    Raises:
        RuntimeError: The CMR query failed.
    """
    page_size = min(limit, 2000)
    url = query._build_url()

    results: List[Any] = []
    more_results = True
    headers = dict(query.headers or {})

    while more_results:
        response = session.get(url, headers=headers, params={"page_size": page_size})

        if cmr_search_after := response.headers.get("cmr-search-after"):
            headers["cmr-search-after"] = cmr_search_after

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            raise RuntimeError(ex.response.text) from ex

        latest = response.json()["items"]

        results.extend(latest)

        more_results = page_size <= len(latest) and len(results) < limit

    return results
