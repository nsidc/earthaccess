import pkg_resources

from .accessor import Accessor
from .auth import Auth
from .search import DataCollections, DataGranules

__all__ = ["DataGranules", "DataCollections", "Auth", "Accessor"]
__version__ = pkg_resources.get_distribution("earthdata").version
