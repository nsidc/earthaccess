from __future__ import annotations

from typing import Any, Callable, Literal, Union

# A VirtualiZarr parser: either a canonical class-name string or a pre-built
# parser instance.  The strings are the exact class names exported from
# ``virtualizarr.parsers`` so that callers can pass them directly without
# importing VirtualiZarr themselves.
ParserType = Union[
    Literal[
        "DMRPPParser",
        "HDFParser",
        "NetCDF3Parser",
        "KerchunkJSONParser",
        "KerchunkParquetParser",
    ],
    Any,
]

AccessType = Literal["direct", "indirect"]
ParallelType = Literal["dask", "lithops", False]
ReferenceFormatType = Literal["json", "parquet"]

# Mirrors xarray.core.types.CompatOptions
CompatType = Literal[
    "identical",
    "equals",
    "broadcast_equals",
    "no_conflicts",
    "override",
    "minimal",
]

# Mirrors xarray.core.types.CombineAttrsOptions
CombineAttrsType = Union[
    Literal["drop", "identical", "no_conflicts", "drop_conflicts", "override"],
    Callable[..., Any],
]

# Mirrors the data_vars parameter of xarray.combine_nested / open_mfdataset
DataVarsType = Union[Literal["all", "minimal", "different"], list[str]]
