import logging

import earthaccess
import magic
import pytest
from earthaccess import Auth, DataGranules, Store

from .param import TestParam
from .sample import get_sample_granules, top_collections_for_provider

logger = logging.getLogger(__name__)


daacs_list: list[TestParam] = [
    {
        "provider_name": "NSIDC_CPRD",
        "n_for_top_collections": 2,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 100,
    },
    {
        "provider_name": "GES_DISC",
        "n_for_top_collections": 2,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 130,
    },
    {
        "provider_name": "POCLOUD",
        "n_for_top_collections": 2,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 100,
    },
    {
        "provider_name": "LPCLOUD",
        "n_for_top_collections": 2,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 100,
    },
    {
        "provider_name": "ORNL_CLOUD",
        "n_for_top_collections": 2,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 50,
    },
]


def supported_collection(data_links):
    return all("podaac-tools.jpl.nasa.gov/drive" not in url for url in data_links)


@pytest.mark.parametrize("daac", daacs_list)
def test_earthaccess_can_open_onprem_collection_granules(daac):
    """Tests that we can open cloud collections using HTTPS links."""
    provider = daac["provider_name"]
    n_for_top_collections = daac["n_for_top_collections"]

    granules_count = daac["granules_count"]
    granules_sample_size = daac["granules_sample_size"]
    granules_max_size = daac["granules_max_size_mb"]

    top_collections = top_collections_for_provider(
        provider,
        n=n_for_top_collections,
    )
    logger.info(f"On-premises collections for {provider}: {len(top_collections)}")

    for concept_id in top_collections:
        granule_query = DataGranules().concept_id(concept_id)
        total_granules = granule_query.hits()
        granules = granule_query.get(granules_count)
        assert len(granules) > 0, "Could not fetch granules"
        assert isinstance(granules[0], earthaccess.DataGranule)
        data_links = granules[0].data_links()
        if not supported_collection(data_links):
            logger.warning(f"PODAAC DRIVE is not supported at the moment: {data_links}")
            continue
        granules_to_open, total_size_cmr = get_sample_granules(
            granules,
            granules_sample_size,
            granules_max_size,
            round_ndigits=2,
        )
        if len(granules_to_open) == 0:
            logger.debug(
                f"Skipping {concept_id}, granule size exceeds configured max size"
            )
            continue
        logger.info(
            f"Testing {concept_id}, granules in collection: {total_granules}, "
            f"download size(MB): {total_size_cmr}"
        )

        store = Store(Auth().login(strategy="environment"))
        # We are testing this method
        fileset = store.open(granules_to_open)

        assert isinstance(fileset, list)

        # we test that we can read some bytes and get the file type
        for file in fileset:
            if not isinstance(file, Exception):
                logger.info(f"File type:  {magic.from_buffer(file.read(2048))}")
            else:
                logger.warning(f"File could not be open: {file}")


def test_multi_file_granule():
    # Ensure granules that contain multiple files are handled correctly
    granules = earthaccess.search_data(short_name="HLSL30", count=1)
    assert len(granules) == 1
    urls = granules[0].data_links()
    assert len(urls) > 1
    files = earthaccess.open(granules)
    assert set(urls) == {f.path for f in files}
