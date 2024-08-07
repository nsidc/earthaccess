import logging
import os
import random
import shutil
import unittest
from collections import TypedDict
from pathlib import Path

import earthaccess
import pytest
from earthaccess import Auth, DataCollections, DataGranules, Store

from .sample import get_sample_granules

logger = logging.getLogger(__name__)


class TestParam(TypedDict):
    daac_name: str

    # How many of the top collections we will test, e.g. top 3 collections
    top_n_collections: int

    # How many granules we will query
    granules_count: int

    # How many granules we will randomly select from the query
    granules_sample_size: int

    # The maximum allowed granule size; if larger we'll try to find another one
    granules_max_size_mb: int


daacs_list: list[TestParam] = [
    {
        "short_name": "NSIDC",
        "top_n_collections": 3,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 100,
    },
    {
        "short_name": "GES_DISC",
        "top_n_collections": 2,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 130,
    },
    {
        "short_name": "LPDAAC",
        "top_n_collections": 2,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 100,
    },
]

assertions = unittest.TestCase("__init__")

# we need to use a valid EDL credential

assertions.assertTrue("EARTHDATA_USERNAME" in os.environ)
assertions.assertTrue("EARTHDATA_PASSWORD" in os.environ)

auth = Auth().login(strategy="environment")
assertions.assertTrue(auth.authenticated)
logger.info(f"Current username: {os.environ['EARTHDATA_USERNAME']}")
logger.info(f"earthaccess version: {earthaccess.__version__}")

store = Store(auth)


def supported_collection(data_links):
    for url in data_links:
        if "podaac-tools.jpl.nasa.gov/drive" in url:
            return False
    return True


@pytest.mark.parametrize("daac", daacs_list)
def test_earthaccess_can_download_onprem_collection_granules(daac):
    """Tests that we can download on-premises collections using HTTPS links."""
    daac_shortname = daac["short_name"]
    collections_count = daac["collections_count"]
    collections_sample_size = daac["collections_sample_size"]
    granules_count = daac["granules_count"]
    granules_sample_size = daac["granules_sample_size"]
    granules_max_size = daac["granules_max_size_mb"]

    collection_query = DataCollections().data_center(daac_shortname).cloud_hosted(False)
    hits = collection_query.hits()
    logger.info(f"On-premises collections for {daac_shortname}: {hits}")
    collections = collection_query.get(collections_count)
    assertions.assertGreater(len(collections), collections_sample_size)
    # We sample n cloud hosted collections from the results
    random_collections = random.sample(collections, collections_sample_size)
    logger.info(f"Sampled {len(random_collections)} collections")
    for collection in random_collections:
        concept_id = collection.concept_id()
        granule_query = DataGranules().concept_id(concept_id)
        total_granules = granule_query.hits()
        granules = granule_query.get(granules_count)
        assertions.assertTrue(len(granules) > 0, "Could not fetch granules")
        assertions.assertTrue(isinstance(granules[0], earthaccess.results.DataGranule))
        data_links = granules[0].data_links()
        if not supported_collection(data_links):
            logger.warning(f"PODAAC DRIVE is not supported at the moment: {data_links}")
            continue
        local_path = f"./tests/integration/data/{concept_id}"
        granules_to_download, total_size_cmr = get_sample_granules(
            granules,
            granules_sample_size,
            granules_max_size,
            round_ndigits=2,
        )
        if len(granules_to_download) == 0:
            logger.debug(
                f"Skipping {concept_id}, granule size exceeds configured max size"
            )
            continue
        logger.info(
            f"Testing {concept_id}, granules in collection: {total_granules}, "
            f"download size(MB): {total_size_cmr}"
        )
        # We are testing this method
        downloaded_results = store.get(granules_to_download, local_path=local_path)

        assertions.assertTrue(isinstance(downloaded_results, list))
        assertions.assertTrue(len(downloaded_results) == granules_sample_size)

        path = Path(local_path)
        assertions.assertTrue(path.is_dir())
        # test that we downloaded the mb reported by CMR
        total_mb_downloaded = round(
            (sum(file.stat().st_size for file in path.rglob("*")) / 1024**2), 2
        )
        # clean the directory
        shutil.rmtree(path)

        # test that we could download the data
        if total_mb_downloaded <= 0:
            logger.warning(f"earthaccess could not download {concept_id}")
        if total_mb_downloaded != total_size_cmr:
            logger.warning(
                f"Warning: {concept_id} downloaded size {total_mb_downloaded}MB is "
                f"different from the size reported by CMR: {total_size_cmr}MB"
            )
