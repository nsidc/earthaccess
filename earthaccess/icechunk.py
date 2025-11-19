from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import earthaccess
import icechunk as ic
from icechunk import IcechunkStore, S3StaticCredentials, s3_storage

from .daac import DAACS

######################## bunch of hardcoded things to revise later ###################
# This should live in DAACs ultimately, but for now lets monkeypatch it for a single case.
# DAACS['PODAAC']['some_new_stuff'] = 'that is really exciting'

# TODO: Review datacube vocab? Do we want to use this? What is a good general term for zarr-ish data?

# TODO: icechunk creds. Test that they persist across expiry? How?

# TODO: Figure out how to ensure authentication here.


def _get_daac_provider_from_url(url: str) -> str:
    # TODO: Hardcoded for initial testing
    return "PODAAC", None


######################################################################################################


class S3IcechunkCredentials:
    def __init__(self, daac: str | None, provider: str | None):
        if daac is None and provider is None:
            raise ValueError("daac and provider cannot both be None")
        self.daac = daac
        self.provider = provider

    def __call__(self) -> S3StaticCredentials:
        # TODO: do I want to assign the auth to this class?
        creds = earthaccess.__auth__.get_s3_credentials(
            daac=self.daac, provider=self.provider
        )
        return S3StaticCredentials(
            access_key_id=creds["accessKeyId"],
            secret_access_key=creds["secretAccessKey"],
            expires_after=datetime.fromisoformat(creds["expiration"]),
            session_token=creds["sessionToken"],
        )


def _open_icechunk_from_url(datacube_url: str) -> IcechunkStore:
    # currently only supports s3
    # How would this support e.g. http, which other protocols make sense?
    # TODO: for now error out on everything that is not s3:
    parsed = urlparse(datacube_url)
    protocol = (
        parsed.scheme or "file"
    )  # not sure this is needed here? will there ever be a need to auth local stores that point to EDL buckets?
    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")

    # match datacube_url to daac (where does the store live?)
    daac, provider = _get_daac_provider_from_url(datacube_url)

    # get auth and init storage for the store based on the protocol
    if protocol == "s3":
        storage = s3_storage(
            bucket=bucket,
            prefix=prefix,
            # get_credentials = S3IcechunkCredentials(daac=daac, provider=provider),
            # TODO: remove for an actual daac store
            anonymous=True,
        )
    else:
        raise NotImplementedError("Currently only s3 is supported as storage protocol.")

    # get config and extract virtual containers
    config = ic.Repository.fetch_config(storage=storage)
    # TODO: accommodate case without virtual chunk containers.
    vchunk_container_urls = config.virtual_chunk_containers.keys()
    print(vchunk_container_urls)

    print(DAACS)

    # check full list of approved container urls against repo
    # TODO: implement an actual check, for now hardcode for test example.
    approved_virtual_container_urls: dict[str, list[str]] = {
        "PODAAC": ["s3://podaac-ops-cumulus-protected/"]
    }

    # Provide appropriate auth for approved virtual container urls
    container_credentials = ic.containers_credentials(
        {
            url: ic.s3_refreshable_credentials(
                S3IcechunkCredentials(daac=daac, provider=None)
            )  # TODO: get provider from the DAACS
            for daac, urls in approved_virtual_container_urls.items()
            for url in urls
        }
    )
    # can we assume that these will always need auth, or will there be public buckets in the mix?

    # open authenticated icechunk repo
    repo = ic.Repository.open(
        storage=storage, authorize_virtual_chunk_access=container_credentials
    )

    # return readonly store from main
    # should this be configurable?
    return repo.readonly_session("main").store
