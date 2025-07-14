"""Generate lists of most popular collections for each of the hardcoded DAACs."""

from pathlib import Path

import requests
from earthaccess.daac import DAACS

THIS_DIR = Path(__file__).parent

# TODO: Can we query CMR for all providers, instead of relying on hard-coded names in a DAAC list?
#   For example, using this URL: "https://cmr.earthdata.nasa.gov/ingest/providers"
all_providers = [
    provider
    for daac_info in DAACS
    for provider in set(
        list(daac_info["cloud-providers"]) + list(daac_info["on-prem-providers"])
    )
]


def top_collections(
    *,
    provider: str,
    num: int = 100,
) -> list[str]:
    if num > 2000:
        raise RuntimeError(
            "Paging not supported, can only get up to 2000 top collections"
        )

    response = requests.post(
        "https://cmr.earthdata.nasa.gov/search/collections.json",
        data={
            "provider": provider,
            "has_granules_or_cwic": True,
            "include_facets": "v2",
            "include_granule_counts": True,
            "include_has_granules": True,
            "include_tags": "edsc.*,opensearch.granule.osdd",
            "page_num": 1,
            "page_size": num,
            "sort_key[]": "-usage_score",
        },
    )
    collection_ids = [
        collection["id"] for collection in response.json()["feed"]["entry"]
    ]
    return collection_ids


def main():
    for provider in all_providers:
        collection_ids = top_collections(provider=provider)

        output = THIS_DIR / f"{provider}.txt"
        output.write_text("\n".join(collection_ids) + "\n")


if __name__ == "__main__":
    main()
