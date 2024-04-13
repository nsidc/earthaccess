"""
Convenience module for importing types from the typing module, abstracting away
the differences between Python versions.
"""

import sys
from typing import Any, Callable, Optional, SupportsFloat, Type, Union, cast

if sys.version_info < (3, 9):
    from typing import Dict, List, Mapping, Sequence, Tuple
else:
    from builtins import dict as Dict, list as List, tuple as Tuple
    from collections.abc import Mapping, Sequence

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override

__all__ = [
    "Any",
    "Callable",
    "Dict",
    "List",
    "Mapping",
    "Optional",
    "Self",
    "Sequence",
    "SupportsFloat",
    "Tuple",
    "Type",
    "TypeAlias",
    "Union",
    "cast",
    "override",
]
