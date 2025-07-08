import logging
import random
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

INTEGRATION_TEST_DIR = Path(__file__).parent
INTEGRATION_TEST_POPULAR_COLLECTIONS_DIR = INTEGRATION_TEST_DIR / "popular_collections"


def top_collections_for_provider(provider: str, *, n: int) -> list[str]:
    """Return the top collections for this provider.

    Local cache is used as the source for this list. Run
    `./popular_collections/generate.py` to refresh it!

    TODO: Skip / exclude collections that have a EULA; filter them out in this function
    or use a pytest skip/xfail mark?
    """
    popular_collections_file = (
        INTEGRATION_TEST_POPULAR_COLLECTIONS_DIR / f"{provider}.txt"
    )
    popular_collections = popular_collections_file.read_text().split("\n")

    return [c for c in popular_collections[:n] if not c.startswith("#")]


def get_sample_granules(
    granules: list,
    sample_size: int,
    max_granule_size: Union[int, float],
    round_ndigits: int | None = None,
):
    """Return a list of randomly-sampled granules and their size in MB.

    Attempt to find only granules smaller or equal to max_granule_size. May return a
    sample smaller than sample_size.
    """
    granules_set = set(granules)

    sample = []
    total_size = 0
    max_tries = sample_size * 2
    tries = 0

    while tries <= max_tries:
        g = random.sample(list(granules_set), 1)[0]
        if g.size() > max_granule_size:
            logger.debug(
                f"Granule {g['meta']['concept-id']} exceeded max size: {g.size()}."
                "Trying another random sample."
            )
            tries += 1
            continue
        else:
            logger.debug(
                f"Adding granule to random sample: {g['meta']['concept-id']} size: {g.size()}"
            )

            sample.append(g)
            granules_set.remove(g)

            total_size += g.size()
            if len(sample) >= sample_size:
                break

    return sample, round(total_size, round_ndigits)
