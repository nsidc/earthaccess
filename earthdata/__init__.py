import pkg_resources

from .auth import Auth
from .search import DataCollections, DataGranules
from .store import Store

__all__ = ["DataGranules", "DataCollections", "Auth", "Store"]
__version__ = pkg_resources.get_distribution("earthdata").version
