from typing import Any, Dict, List, Union

import earthaccess

from .auth import Auth
from .search import DataCollections, DataGranules
from .store import Store
from .utils import _validation as validate


def search_datasets(
    count: int = -1, **kwargs: Any
) -> Union[List[earthaccess.results.DataCollection], None]:
    if not validate.valid_dataset_parameters(**kwargs):
        print(
            "Warning: a valid set of parameters is needed to search for datasets on CMR"
        )
        return None
    query = DataCollections().parameters(**kwargs)
    datasets_found = query.hits()
    print(f"Datasets found: {datasets_found}")
    if count > 0:
        return query.get(count)
    return query.get_all()


def search_data(
    count: int = -1, **kwargs: Any
) -> Union[List[earthaccess.results.DataGranule], None]:
    query = DataGranules().parameters(**kwargs)
    granules_found = query.hits()
    print(f"Granules found: {granules_found}")
    if count > 0:
        return query.get(count)
    return query.get_all()


def login(strategy: str = "interactive") -> Auth:
    """Authenticate with Earthdata login (https://urs.earthdata.nasa.gov/)

    Parameters:

        strategy (String): authentication method.

                "interactive": (default) enter username and password.

                "netrc": retrieve username and password from ~/.netrc.

                "environment": retrieve username and password from $EDL_USERNAME and $EDL_PASSWORD.
        persist (Boolean): will persist credentials in a .netrc file
    Returns:
        an instance of Auth.
    """
    earthaccess.__auth__.login(strategy=strategy)
    return earthaccess.__auth__


def download() -> List[str]:
    return []


def open() -> List[Any]:
    return []


def get_s3_credentials(daac: str, provider: str) -> Dict[str, Any]:
    return {}


def explore() -> None:
    return None
