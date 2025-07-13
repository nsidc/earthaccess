"""Earthdata Environments/Systems module."""

from dataclasses import dataclass

from typing_extensions import NewType

from cmr import CMR_OPS, CMR_UAT

CMRBaseURL = NewType("CMRBaseURL", str)
EDLHostname = NewType("EDLHostname", str)
StatusURL = NewType("StatusURL", str)
StatusApiURL = NewType("StatusApiURL", str)

STATUS_PROD_URL = "https://status.earthdata.nasa.gov/"
STATUS_UAT_URL = "https://status.uat.earthdata.nasa.gov/"
STATUS_API_PROD_URL = "https://status.earthdata.nasa.gov/api/v1/statuses"
STATUS_API_UAT_URL = "https://status.uat.earthdata.nasa.gov/api/v1/statuses"


@dataclass(frozen=True)
class System:
    """Host URL options, for different Earthdata domains."""

    cmr_base_url: CMRBaseURL
    status_url: StatusURL
    status_api_url: StatusApiURL
    edl_hostname: EDLHostname


PROD = System(
    CMRBaseURL(CMR_OPS),
    StatusURL(STATUS_PROD_URL),
    StatusApiURL(STATUS_API_PROD_URL),
    EDLHostname("urs.earthdata.nasa.gov"),
)
UAT = System(
    CMRBaseURL(CMR_UAT),
    StatusURL(STATUS_UAT_URL),
    StatusApiURL(STATUS_API_UAT_URL),
    EDLHostname("uat.urs.earthdata.nasa.gov"),
)
