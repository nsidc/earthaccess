import logging
import threading
from importlib.metadata import version
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
    open,
    search_data,
    search_datasets,
    search_services,
)
from .auth import Auth
from .zarr import open_virtual_dataset, open_virtual_mfdataset, consolidate_metadata, get_virtual_reference
from .search import DataCollection, DataCollections, DataGranule, DataGranules
from .services import DataServices
from .store import Store
from .system import PROD, UAT

logger = logging.getLogger(__name__)

__all__ = [
    # api.py
    "login",
    "search_datasets",
    "search_data",
    "search_services",
    "get_requests_https_session",
    "get_fsspec_https_session",
    "get_s3fs_session",
    "get_s3_credentials",
    "get_s3_filesystem",
    "get_edl_token",
    "granule_query",
    "collection_query",
    "open",
    "download",
    "auth_environ",
    # search.py
    "DataGranule",
    "DataGranules",
    "DataCollection",
    "DataCollections",
    "DataServices",
    # auth.py
    "Auth",
    # store.py
    "Store",
    # kerchunk
    "consolidate_metadata",
    "get_virtual_reference",
    # virtualizarr
    "open_virtual_dataset",
    "open_virtual_mfdataset",
    "PROD",
    "UAT",
]

__version__ = version("earthaccess")

_auth = Auth()
_store: Optional[Store] = None
_lock = threading.Lock()


def __getattr__(name):  # type: ignore
    """Module-level getattr to handle automatic authentication when accessing
    `earthaccess.__auth__` and `earthaccess.__store__`.

    Other unhandled attributes raise as `AttributeError` as expected.
    """
    global _auth, _store

    if name not in ["__auth__", "__store__"]:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    with _lock:
        if not _auth.authenticated:
            for strategy in ["environment", "netrc"]:
                try:
                    _auth.login(strategy=strategy)

                    if _auth.authenticated:
                        _store = Store(_auth)
                        logger.debug(
                            f"Automatic authentication with {strategy=} was successful"
                        )
                        break
                except Exception as e:
                    logger.debug(
                        f"An error occurred during automatic authentication with {strategy=}: {str(e)}"
                    )

        return _auth if name == "__auth__" else _store
