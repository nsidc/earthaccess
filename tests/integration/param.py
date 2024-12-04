from typing import TypedDict


class TestParam(TypedDict):
    provider_name: str

    # How many of the top collections we will test, e.g. top 3 collections
    n_for_top_collections: int

    # How many granules we will query
    granules_count: int

    # How many granules we will randomly select from the query
    granules_sample_size: int

    # The maximum allowed granule size; if larger we'll try to find another one
    granules_max_size_mb: int
