"""Earthdata Environments/Systems module."""

from dataclasses import dataclass

from typing_extensions import NewType

from cmr import CMR_OPS, CMR_UAT

CMRBaseURL = NewType("CMRBaseURL", str)
EDLHostname = NewType("EDLHostname", str)


@dataclass(frozen=True)
class System:
    """Host URL options, for different Earthdata domains."""

    cmr_base_url: CMRBaseURL
    edl_hostname: EDLHostname


PROD = System(CMRBaseURL(CMR_OPS), EDLHostname("urs.earthdata.nasa.gov"))
UAT = System(CMRBaseURL(CMR_UAT), EDLHostname("uat.urs.earthdata.nasa.gov"))
