import json
import earthaccess
from pystac_client import Client
from pystac import Item, ItemCollection
from pprint import pprint

earthaccess.login()

ITEM_COUNT=5

# This should select only one granule: `HLS.L30.T15RYP.2025305T163224.v2.0`
COLLECTION="HLSL30"
DATE_START="2025-11-01"
DATE_END="2025-11-04"
XMIN, YMIN, XMAX, YMAX = -90.621777,30.482727,-90.521931,30.582727


def _fetch_earthaccess_native() -> list[earthaccess.DataGranule]:
    earthaccess.login()
    granules = earthaccess.search_data(
        short_name=COLLECTION,
        count=ITEM_COUNT,
        temporal=(DATE_START, DATE_END),
        bounding_box=(XMIN, YMIN, XMAX, YMAX)
    )
    
    return granules


def _granule_to_stac_json(g) -> dict:
    # ... do some stuff ...
    # Core fields: assets, geometry, time

    return {
        "id": g["meta"]["native-id"],
        "assets": {

        },
        "bbox": ...,
        "collection": ...,
        "geometry": {
            "coordinates": [[
                [..., ...],
                [..., ...],
                
            ]],
            "type": "Polygon",
        },
        "links": [
            {...},
            {...},
        ],
        "properties": {
            "datetime": ...,
            "start_datetime": ...,
            "end_datetime": ...,
            "eo:cloud_cover": ...,
            "storage:schemes": {...}, 
        },
        "stac_extensions": [..., ...],
        "stac_version": "1.1.0",
        "type": "Feature",

    }


def fetch_stac_native() -> list[dict]:
    conn = Client.open("https://cmr.earthdata.nasa.gov/stac/LPCLOUD")
    items = conn.search(
        collections=["HLSL30_2.0"],
        # max_items=ITEM_COUNT,  # 14 million total
        datetime=f"{DATE_START}/{DATE_END}",
        bbox=(XMIN, YMIN, XMAX, YMAX),
        # sortby=...,
    ).items()

    return [i.to_dict() for i in items]


def main():
    granules_earthaccess = _fetch_earthaccess_native()
    #items_earthaccess = [_granule_to_item(g) for g in granules_earthaccess]

    items_stac = fetch_stac_native()
    pprint(items_stac)
    # print(f"{len(items_stac)=}")

    print("STAC IDs:", " ".join(i["id"] for i in items_stac))
    print("EA IDs:", " ".join(g["meta"]["native-id"] for g in granules_earthaccess))
    
    # assert sorted(fetch_stac_earthaccess()) == sorted(fetch_stac_native())


if __name__ == "__main__":
    main()