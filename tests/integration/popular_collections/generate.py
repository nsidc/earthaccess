"""Generate lists of most popular collections for each of the hardcoded DAACs."""

from pathlib import Path

import requests

THIS_DIR = Path(__file__).parent


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
    # TODO: Can we query CMR for all providers? Then cache the top collections for all
    # providers?
    for provider in ["NSIDC_ECS"]:
        collection_ids = top_collections(provider="NSIDC_ECS")

        output = THIS_DIR / f"{provider}.txt"
        with output.open("w") as f:
            f.write("\n".join(collection_ids))


if __name__ == "__main__":
    main()
