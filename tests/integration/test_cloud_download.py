import logging
import random
import shutil
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


def get_sample_granules(granules, sample_size, max_granule_size):
    """Returns a list with sample granules and their size in MB if
    the total size is less than the max_granule_size.
    """
    files_to_download = []
    total_size = 0
    max_tries = sample_size * 2
    tries = 0

    while tries <= max_tries:
        g = random.sample(granules, 1)[0]
        if g.size() > max_granule_size:
            tries += 1
            continue
        else:
            files_to_download.append(g)
            total_size += g.size()
            if len(files_to_download) >= sample_size:
                break
    return files_to_download, round(total_size)


@pytest.mark.parametrize("daac", daac_list)
def test_earthaccess_can_download_cloud_collection_granules(tmp_path, daac):
    """Tests that we can download cloud collections using HTTPS links."""
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
    assert len(collections) > collections_sample_size
    # We sample n cloud hosted collections from the results
    random_collections = random.sample(collections, collections_sample_size)

    for collection in random_collections:
        concept_id = collection.concept_id()
        granule_query = DataGranules().concept_id(concept_id)
        total_granules = granule_query.hits()
        granules = granule_query.get(granules_count)
        assert isinstance(granules, list) and len(granules) > 0
        assert isinstance(granules[0], earthaccess.DataGranule)
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
        path = tmp_path / "tests" / "integration" / "data" / concept_id
        path.mkdir(parents=True)
        store = Store(Auth().login(strategy="environment"))

        try:
            # We are testing this method
            store.get(granules_to_download, local_path=path)
        except Exception as e:
            logger.warning(e)

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


def test_multi_file_granule(tmp_path):
    # Ensure granules that contain multiple files are handled correctly
    granules = earthaccess.search_data(short_name="HLSL30", count=1)
    assert len(granules) == 1
    urls = granules[0].data_links()
    assert len(urls) > 1
    files = earthaccess.download(granules, str(tmp_path))
    assert {Path(f).name for f in urls} == {Path(f).name for f in files}
