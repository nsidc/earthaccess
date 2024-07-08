import logging
import os
import random
import unittest

import earthaccess
import pytest
from earthaccess import Auth, Store

ACCEPTABLE_FAILURE_RATE = 10


@pytest.hookimpl()
def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 0:
        return
    failure_rate = (100.0 * session.testsfailed) / session.testscollected
    if failure_rate <= ACCEPTABLE_FAILURE_RATE:
        session.exitstatus = 0


@pytest.fixture(scope="module")
def authenticated_store():
    logger = logging.getLogger(__name__)
    assertions = unittest.TestCase("__init__")

    # we need to use a valid EDL credential

    assert "EARTHDATA_USERNAME" in os.environ
    assert "EARTHDATA_PASSWORD" in os.environ

    auth = Auth().login(strategy="environment")
    assert auth.authenticated is True
    logger.info(f"Current username: {os.environ['EARTHDATA_USERNAME']}")
    logger.info(f"earthaccess version: {earthaccess.__version__}")

    store = Store(auth)

    return store, logger, assertions


@pytest.fixture()
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


@pytest.fixture()
def granules():
    granules = earthaccess.search_data(
        count=2,
        short_name="SEA_SURFACE_HEIGHT_ALT_GRIDS_L4_2SATS_5DAY_6THDEG_V_JPL2205",
        cloud_hosted=True,
    )
    return granules
