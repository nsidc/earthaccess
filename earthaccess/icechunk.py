from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import earthaccess
import icechunk as ic
from icechunk import IcechunkStore, S3StaticCredentials, s3_storage

import warnings

######################## bunch of hardcoded things to revise later ###################
# As discussed in https://github.com/nsidc/earthaccess/pull/1135 this should be stored
# independent from the code. Will be implemented in a separate PR that needs to be
# merged before this one.

credential_endpoint_mapping = {
  "TestBucket": "www.testexample.com",
  "asdc-prod-protected": "https://data.asdc.earthdata.nasa.gov/s3credentials",
  "asf-cumulus-prod-alos2-products": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
  "asf-cumulus-prod-aria-products": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
  "asf-cumulus-prod-browse": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
  "asf-cumulus-prod-opera-browse/OPERA_L2_CSLC-S1": "https://cumulus.asf.alaska.edu/s3credentials",
  "asf-cumulus-prod-opera-browse/OPERA_L2_RTC-S1": "https://cumulus.asf.alaska.edu/s3credentials",
  "asf-cumulus-prod-opera-browse/OPERA_L4_TROPO-ZENITH_V1": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
  "asf-cumulus-prod-opera-product": "https://cumulus.asf.alaska.edu/s3credentials",
  "asf-cumulus-prod-opera-products/OPERA_L2_CSLC-S1": "https://cumulus.asf.alaska.edu/s3credentials",
  "asf-cumulus-prod-opera-products/OPERA_L2_CSLC-S1_STATIC": "https://cumulus.asf.alaska.edu/s3credentials",
  "asf-cumulus-prod-opera-products/OPERA_L2_RTC-S1": "https://cumulus.asf.alaska.edu/s3credentials",
  "asf-cumulus-prod-opera-products/OPERA_L2_RTC-S1_STATIC": "https://cumulus.asf.alaska.edu/s3credentials",
  "asf-cumulus-prod-opera-products/OPERA_L4_TROPO-ZENITH_V1": "https://cumulus.asf.earthdatacloud.nasa.gov/s3credentials",
  "asf-cumulus-prod-seasat-products": "https://cumulus.asf.alaska.edu/s3credentials",
  "asf-ngap2w-p-s1-grd-7d1b4348": "https://sentinel1.asf.alaska.edu/s3credentials",
  "asf-ngap2w-p-s1-ocn-1e29d408": "https://sentinel1.asf.alaska.edu/s3credentials",
  "asf-ngap2w-p-s1-raw-98779950": "https://sentinel1.asf.alaska.edu/s3credentials",
  "asf-ngap2w-p-s1-slc-7b420b89": "https://sentinel1.asf.alaska.edu/s3credentials",
  "asf-ngap2w-p-s1-xml-8cf7476b": "https://sentinel1.asf.alaska.edu/s3credentials",
  "csda-cumulus-prod-protected-5047": "https://data.csdap.earthdata.nasa.gov/s3credentials",
  "gesdisc-cumulus-prod-protected": "https://data.gesdisc.earthdata.nasa.gov/s3credentials",
  "gesdisc-cumulus-prod-protectedAqua_AIRS_Level2": "https://data.gesdisc.earthdata.nasa.gov/s3credentials",
  "ghrcw-protected": "https://data.ghrc.earthdata.nasa.gov/s3credentials",
  "ghrcwuat-protected": "https://data.ghrc.uat.earthdata.nasa.gov/s3credentials",
  "lp-prod-protected": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
  "lp-prod-public": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
  "lp-protected": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
  "lp-public": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
  "lp-sit-protected": "https://data.lpdaac.sit.earthdatacloud.nasa.gov/s3credentials",
  "lp-sit-public": "https://data.lpdaac.sit.earthdatacloud.nasa.gov/s3credentials",
  "nsidc-cumulus-prod-protected": "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
  "nsidc-cumulus-prod-public": "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
  "ob-cumulus-prod-public": "https://obdaac-tea.earthdatacloud.nasa.gov/s3credentials",
  "ob-cumulus-sit-public": "https://obdaac-tea.sit.earthdatacloud.nasa.gov/s3credentials",
  "ob-cumulus-uat-public": "https://obdaac-tea.uat.earthdatacloud.nasa.gov/s3credentials",
  "ornl-cumulus-prod-protected": "https://data.ornldaac.earthdata.nasa.gov/s3credentials",
  "ornl-cumulus-prod-public": "https://data.ornldaac.earthdata.nasa.gov/s3credentials",
  "podaac-ops-cumulus-docs": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
  "podaac-ops-cumulus-protected": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
  "podaac-ops-cumulus-public": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
  "podaac-swot-ops-cumulus-protected": "https://archive.swot.podaac.earthdata.nasa.gov/s3credentials",
  "podaac-swot-ops-cumulus-public": "https://archive.swot.podaac.earthdata.nasa.gov/s3credentials",
  "prod-lads": "https://data.laadsdaac.earthdatacloud.nasa.gov/s3credentials"
}

################################################################################

def _get_credential_endpoint(url: str) -> str:
    sep = '/'
    parsed = urlparse(url)
    if parsed.scheme != 's3':
        raise ValueError('Only s3 is supported as storage protocol. Got {parsed.protocol}')
        #TODO: Is protocol the right vocabulary here?
    bucket_w_prefix_full = parsed.netloc + parsed.path.rstrip(sep)
    components = bucket_w_prefix_full.split(sep)


    while len(components) > 0:
        partial_target = sep.join(components)
        if partial_target in credential_endpoint_mapping.keys():
            return credential_endpoint_mapping[partial_target]
        components = components [0:-1]
        
    raise ValueError('Could not find any matching credential enpoint for {url}')


class S3IcechunkCredentials:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def __call__(self) -> S3StaticCredentials:
        creds = earthaccess.__auth__.get_s3_credentials(
            endpoint=self.endpoint
        )
        return S3StaticCredentials(
            access_key_id=creds["accessKeyId"],
            secret_access_key=creds["secretAccessKey"],
            expires_after=datetime.fromisoformat(creds["expiration"]),
            session_token=creds["sessionToken"],
        )

def get_virtual_chunk_credentials(storage: ic.Storage) -> dict[str, ic.AnyCredential | None]:
    """Function to retrive virtual chunk containers from icechunk storage and authenticate 
    all allowed virtual chunk prefixes using EDL credentials"""
    # get config and extract virtual containers
    config = ic.Repository.fetch_config(storage=storage)
    # TODO: accommodate case without virtual chunk containers.
    vchunk_container_urls = config.virtual_chunk_containers.keys()

    # try to build authentication for all virtual chunk containers. If any of the virtual 
    # chunk containes is not 'approved' it will raise an error in `_get_credential_endpoint`.
    # We will catch the error here, warn, and only return the authenticated urls. 
    # Users will then get an error for the remaining containers and need to add thes manually!
    failed_container_urls = []
    credential_mapping = {}
    for url in vchunk_container_urls:
        try:
            endpoint = _get_credential_endpoint(url)
            credential_mapping[url] = ic.s3_refreshable_credentials(
                S3IcechunkCredentials(endpoint=endpoint)
            ) 
        except ValueError:
            failed_container_urls.append(url)

    if len(failed_container_urls) > 0:
        #TODO: link to credentials in icechunk + docs about the endpoint registry
        warnings.warn(f'Could not build virtual chunk credentials for {failed_container_urls}.\
                      If the URL is a non EDL bucket, you have to manually construct credentials (...)')

    #TODO: Check how easy it is to 'splice' this output with manuall created credentials
    return ic.containers_credentials(credential_mapping)

# TODO: Review datacube vocab? Do we want to use this? What is a good general term for zarr-ish data?

def open_icechunk_from_url(
        datacube_url: str,
        ) -> IcechunkStore:
    """ Opener function for 'full' EDL icechunk stores, meaning both the icechunk store and the
    target chunks are in an EDL authenticated bucket.
    In case that you are accessing an icechunk store on another storage location, with
    virtual chunks pointing to EDL buckets use `earthaccess.icechunk.get_virtual_chunk_credentials`
    directly:
    ```
    import icechunk as ic
    from earthaccess.icechunk import get_virtual_chunk_credentials
    storage = ... # configure your custom icechunk storage
    vchunk_credentials = get_virtual_chunk_credentials(storage)
    repo = ic.Repository.open(storage=storage, authorize_virtual_chunk_access=vchunk_credentials)
    ...
    ```
    """
    # currently only supports s3
    # How would this support e.g. http, which other protocols make sense?
    # TODO: for now error out on everything that is not s3:
    parsed = urlparse(datacube_url)
    protocol = (
        parsed.scheme or "file"
    )  # not sure this is needed here? will there ever be a need to auth local stores that point to EDL buckets?
    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")

    # find credential endpoint
    endpoint = _get_credential_endpoint(url)

    # get auth and init storage for the store based on the protocol
    if protocol == "s3":
        storage = s3_storage(
            bucket=bucket,
            prefix=prefix,
            get_credentials = S3IcechunkCredentials(endpoint=endpoint),
        )
    else:
        raise NotImplementedError("Currently only s3 is supported as storage protocol.")

    virtual_chunk_credentials = get_virtual_chunk_credentials(storage)

    # open authenticated icechunk repo
    repo = ic.Repository.open(
        storage=storage, 
        authorize_virtual_chunk_access=virtual_chunk_credentials
    )

    # return readonly store from main
    # TODO: should this be configurable?
    return repo.readonly_session("main").store

