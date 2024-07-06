import logging
import random

logger = logging.getLogger(__name__)


def get_sample_granules(
    granules: list,
    sample_size: int,
    max_granule_size: int | float,
    round_ndigits: int = None,
):
    """Return a list of randomly-sampled granules and their size in MB.

    Attempt to find only granules smaller or equal to max_granule_size. May return a
    sample smaller than sample_size.
    """
    sample = []
    total_size = 0
    max_tries = sample_size * 2
    tries = 0

    while tries <= max_tries:
        g = random.sample(granules, 1)[0]
        if g.size() > max_granule_size:
            logger.debug(
                f"Granule {g['meta']['concept-id']} exceded max size: {g.size()}."
                "Trying another random sample."
            )
            tries += 1
            continue
        else:
            logger.debug(
                f"Adding granule to random sample: {g['meta']['concept-id']} size: {g.size()}"
            )
            sample.append(g)
            total_size += g.size()
            if len(sample) >= sample_size:
                break

    return sample, round(total_size, round_ndigits)
