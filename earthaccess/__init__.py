import threading
from importlib.metadata import version
from typing import Any

from .api import (
    collection_query,
    download,
    get_fsspec_https_session,
    get_requests_https_session,
    get_s3_credentials,
    get_s3fs_session,
    granule_query,
    login,
    open,
    search_data,
    search_datasets,
)
from .auth import Auth
from .search import DataCollections, DataGranules
from .store import Store

__all__ = [
    "login",
    "search_datasets",
    "search_data",
    "get_requests_https_session",
    "get_fsspec_https_session",
    "get_s3fs_session",
    "get_s3_credentials",
    "granule_query",
    "collection_query",
    "open",
    "download",
    "DataGranules",
    "DataCollections",
    "Auth",
    "Store",
]

__version__ = version("earthaccess")

_auth = Auth()
_store = None
_lock = threading.Lock()


def __getattr__(name):  # type: ignore
    global _auth, _store

    if name == "__auth__" or name == "__store__":
        with _lock:
            if not _auth.authenticated:
                for strategy in ["environment", "netrc"]:
                    try:
                        _auth.login(strategy=strategy)
                    except Exception:
                        continue
                    else:
                        if not _auth.authenticated:
                            continue
                        else:
                            _store = Store(_auth)
                            break
            return _auth if name == "__auth__" else _store
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
