from __future__ import annotations

from typing import Any, Literal, Union

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
