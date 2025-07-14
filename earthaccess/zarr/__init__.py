from .dmrpp_zarr import open_virtual_dataset, open_virtual_mfdataset
from .kerchunk import consolidate_metadata, get_virtual_reference

__all__ = [
    "consolidate_metadata",
    "open_virtual_dataset",
    "open_virtual_mfdataset",
    "get_virtual_reference",
]
