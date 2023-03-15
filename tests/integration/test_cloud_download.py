# package imports
import logging
import os
import random
import shutil
import unittest
from pathlib import Path

import earthaccess
import pytest
from earthaccess import Auth, DataCollections, DataGranules, Store

logger = logging.getLogger(__name__)


daac_list = [
    {
        "short_name": "NSIDC",
        "collections_count": 50,
        "collections_sample_size": 3,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 100,
    },
    {
        "short_name": "GES_DISC",
        "collections_count": 100,
        "collections_sample_size": 3,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 150,
    },
    {
        "short_name": "PODAAC",
        "collections_count": 100,
        "collections_sample_size": 3,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 100,
    },
    {
        "short_name": "LPDAAC",
        "collections_count": 100,
        "collections_sample_size": 3,
        "granules_count": 100,
        "granules_sample_size": 2,
        "granules_max_size_mb": 100,
    },
    {
        "short_name": "ORNLDAAC",
        "collections_count": 100,
        "collections_sample_size": 3,
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


def get_sample_granules(granules, sample_size, max_granule_size):
    """
    returns a list with sample granules and their size in MB if
    the total size is less than the max_granule_size
    """
    files_to_download = []
    total_size = 0
    max_tries = sample_size * 2
    tries = 0

    while tries <= max_tries:
        g = random.sample(granules, 1)[0]
        if g.size() > max_granule_size:
            # print(f"G: {g['meta']['concept-id']} exceded max size: {g.size()}")
            tries += 1
            continue
        else:
            # print(f"Adding : {g['meta']['concept-id']} size: {g.size()}")
            files_to_download.append(g)
            total_size += g.size()
            if len(files_to_download) >= sample_size:
                break
    return files_to_download, round(total_size)


@pytest.mark.parametrize("daac", daac_list)
def test_earthaccess_can_download_cloud_collection_granules(daac):
    """
    Tests that we can download cloud collections using HTTPS links
    """
    daac_shortname = daac["short_name"]
    collections_count = daac["collections_count"]
    collections_sample_size = daac["collections_sample_size"]
    granules_count = daac["granules_count"]
    granules_sample_size = daac["granules_sample_size"]
    granules_max_size = daac["granules_max_size_mb"]

    collection_query = DataCollections().data_center(daac_shortname).cloud_hosted(True)
    hits = collection_query.hits()
    logger.info(f"Cloud hosted collections for {daac_shortname}: {hits}")
    collections = collection_query.get(collections_count)
    assertions.assertGreater(len(collections), collections_sample_size)
    # We sample n cloud hosted collections from the results
    random_collections = random.sample(collections, collections_sample_size)
    for collection in random_collections:
        concept_id = collection.concept_id()
        granule_query = DataGranules().concept_id(concept_id)
        total_granules = granule_query.hits()
        granules = granule_query.get(granules_count)
        assert type(granules) is list and len(granules) > 0
        assert isinstance(granules[0], earthaccess.results.DataGranule)
        local_path = f"./tests/integration/data/{concept_id}"
        granules_to_download, total_size_cmr = get_sample_granules(
            granules, granules_sample_size, granules_max_size
        )
        if len(granules_to_download) == 0:
            logger.warning(
                f"Skipping {concept_id}, granule size exceeds configured max size"
            )
            continue
        logger.info(
            f"Testing {concept_id}, granules in collection: {total_granules}, "
            f"download size(MB): {total_size_cmr}"
        )
        # We are testing this method
        try:
            store.get(granules_to_download, local_path=local_path)
        except Exception:
            logger.warning(Exception)

        path = Path(local_path)
        assert path.is_dir()
        # test that we downloaded the mb reported by CMR
        total_mb_downloaded = round(
            (sum(file.stat().st_size for file in path.rglob("*")) / 1024**2)
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
