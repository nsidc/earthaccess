# DAACS ~= NASA Earthdata data centers
from typing import Union

DAACS = [
    {
        "short-name": "NSIDC",
        "name": "National Snow and Ice Data Center",
        "homepage": "https://nsidc.org",
        "cloud-providers": ["NSIDC_CPRD"],
        "on-prem-providers": ["NSIDC_ECS"],
        "s3-credentials": "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
    },
    {
        "short-name": "GHRCDAAC",
        "name": "Global Hydrometeorology Resource Center",
        "homepage": "https://ghrc.nsstc.nasa.gov/home/",
        "cloud-providers": ["GHRC_DAAC"],
        "on-prem-providers": ["GHRC_DAAC"],
        "s3-credentials": "https://data.ghrc.earthdata.nasa.gov/s3credentials",
    },
    {
        "short-name": "PODAAC",
        "name": "Physical Oceanography Distributed Active Archive Center",
        "homepage": "https://podaac.jpl.nasa.gov",
        "cloud-providers": ["POCLOUD"],
        "on-prem-providers": ["PODAAC"],
        "s3-credentials": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
    },
    {
        "short-name": "ASF",
        "name": "Alaska Satellite Facility",
        "homepage": "https://asf.alaska.edu",
        "cloud-providers": ["ASF"],
        "on-prem-providers": ["ASF"],
        "s3-credentials": "",
    },
    {
        "short-name": "ORNLDAAC",
        "name": "Oak Ridge National Laboratory",
        "homepage": "https://daac.ornl.gov",
        "cloud-providers": ["ORNL_CLOUD"],
        "on-prem-providers": ["ORNL_DAAC"],
        "s3-credentials": "https://data.ornldaac.earthdata.nasa.gov/s3credentials",
    },
    {
        "short-name": "LPDAAC",
        "name": " Land Processes Distributed Active Archive Center",
        "homepage": "https://lpdaac.usgs.gov",
        "cloud-providers": ["LPCLOUD"],
        "on-prem-providers": ["LPDAAC_ECS"],
        "s3-credentials": "https://data.lpdaac.prod.earthdatacloud.nasa.gov/s3credentials",
    },
    {
        "short-name": "GESDISC",
        "name": "NASA Goddard Earth Sciences (GES) Data and Information Services Center (DISC)",
        "homepage": "https://daac.gsfc.nasa.gov",
        "cloud-providers": ["GES_DISC"],
        "on-prem-providers": ["GES_DISC"],
        "s3-credentials": "",
    },
    {
        "short-name": "OBDAAC",
        "name": "NASA's Ocean Biology Distributed Active Archive Center",
        "homepage": "https://earthdata.nasa.gov/eosdis/daacs/obdaac",
        "cloud-providers": [],
        "on-prem-providers": ["OB_DAAC"],
        "s3-credentials": "",
    },
    {
        "short-name": "SEDAC",
        "name": "NASA's Socioeconomic Data and Applications Center",
        "homepage": "https://earthdata.nasa.gov/eosdis/daacs/sedac",
        "cloud-providers": [],
        "on-prem-providers": ["SEDAC"],
        "s3-credentials": "",
    },
]


CLOUD_PROVIDERS = [
    "GES_DISC",
    "LPCLOUD",
    "NSIDC_CPRD",
    "POCLOUD",
    "ASF",
    "GHRC_DAAC",
    "ORNL_CLOUD",
]


def find_provider(
    daac_short_name: str = None, cloud_hosted: bool = None
) -> Union[str, None]:
    for daac in DAACS:
        if daac_short_name == daac["short-name"]:
            if cloud_hosted:
                if len(daac["cloud-providers"]) > 0:
                    return daac["cloud-providers"][0]
                else:
                    # We found the DAAC but it does not have cloud data
                    return daac["on-prem-providers"][0]
            else:
                # return on prem provider code
                return daac["on-prem-providers"][0]
    return None
