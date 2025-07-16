"""Earthdata Environments/Systems module."""

from dataclasses import dataclass

from typing_extensions import NewType

from cmr import CMR_OPS, CMR_UAT

CMRBaseURL = NewType("CMRBaseURL", str)
EDLHostname = NewType("EDLHostname", str)
StatusURL = NewType("StatusURL", str)
StatusApiURL = NewType("StatusApiURL", str)


@dataclass(frozen=True)
class System:
    """Host URL options, for different Earthdata domains."""

    cmr_base_url: CMRBaseURL
    status_url: StatusURL
    status_api_url: StatusApiURL
    edl_hostname: EDLHostname


PROD = System(
    CMRBaseURL(CMR_OPS),
    StatusURL("https://status.earthdata.nasa.gov/"),
    StatusApiURL("https://status.earthdata.nasa.gov/api/v1/statuses"),
    EDLHostname("urs.earthdata.nasa.gov"),
)
UAT = System(
    CMRBaseURL(CMR_UAT),
    StatusURL("https://status.uat.earthdata.nasa.gov/"),
    StatusApiURL("https://status.uat.earthdata.nasa.gov/api/v1/statuses"),
    EDLHostname("uat.urs.earthdata.nasa.gov"),
)
