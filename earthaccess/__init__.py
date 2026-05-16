import logging
import threading
from typing import Optional

from .api import (
    auth_environ,
    collection_query,
    download,
    get_edl_token,
    get_fsspec_https_session,
    get_requests_https_session,
    get_s3_credentials,
    get_s3_filesystem,
    get_s3fs_session,
    granule_query,
    login,
    open,  # noqa: A004
    search_data,
    search_datasets,
    search_services,
    status,
)
from .auth import Auth
from .search import DataCollection, DataCollections, DataGranule, DataGranules
from .services import DataServices
from .store import Store
from .system import PROD, UAT
from .virtual import virtualize

logger = logging.getLogger(__name__)

__all__ = [
    # system.py
    "PROD",
    "UAT",
    # auth.py
    "Auth",
    # search.py
    "DataCollection",
    "DataCollections",
    "DataGranule",
    "DataGranules",
    "DataServices",
    # store.py
    "Store",
    # api.py
    "auth_environ",
    "collection_query",
    "download",
    "get_edl_token",
    "get_fsspec_https_session",
    "get_requests_https_session",
    "get_s3_credentials",
    "get_s3_filesystem",
    "get_s3fs_session",
    "granule_query",
    "login",
    "open",
    "search_data",
    "search_datasets",
    "search_services",
    "status",
    # virtual
    "virtualize",
]

try:
    from ._version import version as __version__
except ImportError:
    from importlib.metadata import version as get_version

    __version__ = get_version("earthaccess")

_auth = Auth()
_store: Store | None = None
_lock = threading.Lock()


def __getattr__(name):  # type: ignore
    """Module-level getattr to handle automatic authentication when accessing
    `earthaccess.__auth__` and `earthaccess.__store__`.

    Other unhandled attributes raise as `AttributeError` as expected.
    """
    global _auth, _store

    if name not in ["__auth__", "__store__"]:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)

    return _auth if name == "__auth__" else _store
