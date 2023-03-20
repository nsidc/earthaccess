# DAACS ~= NASA Earthdata data centers
from typing import Optional, Union

import requests

DAACS = [
    {
        "short-name": "NSIDC",
        "name": "National Snow and Ice Data Center",
        "homepage": "https://nsidc.org",
        "cloud-providers": ["NSIDC_CPRD"],
        "on-prem-providers": ["NSIDC_ECS"],
        "s3-credentials": "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "GHRCDAAC",
        "name": "Global Hydrometeorology Resource Center",
        "homepage": "https://ghrc.nsstc.nasa.gov/home/",
        "cloud-providers": ["GHRC_DAAC"],
        "on-prem-providers": ["GHRC_DAAC"],
        "s3-credentials": "https://data.ghrc.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "PODAAC",
        "name": "Physical Oceanography Distributed Active Archive Center",
        "homepage": "https://podaac.jpl.nasa.gov",
        "cloud-providers": ["POCLOUD"],
        "on-prem-providers": ["PODAAC"],
        "s3-credentials": "https://archive.podaac.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "ASF",
        "name": "Alaska Satellite Facility",
        "homepage": "https://asf.alaska.edu",
        "cloud-providers": ["ASF"],
        "on-prem-providers": ["ASF"],
        "s3-credentials": "https://sentinel1.asf.alaska.edu/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "ORNLDAAC",
        "name": "Oak Ridge National Laboratory",
        "homepage": "https://daac.ornl.gov",
        "cloud-providers": ["ORNL_CLOUD"],
        "on-prem-providers": ["ORNL_DAAC"],
        "s3-credentials": "https://data.ornldaac.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "LPDAAC",
        "name": " Land Processes Distributed Active Archive Center",
        "homepage": "https://lpdaac.usgs.gov",
        "cloud-providers": ["LPCLOUD"],
        "on-prem-providers": ["LPDAAC_ECS"],
        "s3-credentials": "https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "GES_DISC",
        "name": "NASA Goddard Earth Sciences (GES) Data and Information Services Center (DISC)",
        "homepage": "https://daac.gsfc.nasa.gov",
        "cloud-providers": ["GES_DISC"],
        "on-prem-providers": ["GES_DISC"],
        "s3-credentials": "https://data.gesdisc.earthdata.nasa.gov/s3credentials",
        "eulas": [],
    },
    {
        "short-name": "OBDAAC",
        "name": "NASA's Ocean Biology Distributed Active Archive Center",
        "homepage": "https://earthdata.nasa.gov/eosdis/daacs/obdaac",
        "cloud-providers": [],
        "on-prem-providers": ["OB_DAAC"],
        "s3-credentials": "",
        "eulas": [],
    },
    {
        "short-name": "SEDAC",
        "name": "NASA's Socioeconomic Data and Applications Center",
        "homepage": "https://earthdata.nasa.gov/eosdis/daacs/sedac",
        "cloud-providers": [],
        "on-prem-providers": ["SEDAC"],
        "s3-credentials": "",
        "eulas": [],
    },
    {
        "short-name": "LAADS",
        "name": "Level-1 and Atmosphere Archive & Distribution System Distributed Active Archive Center",
        "homepage": "https://ladsweb.modaps.eosdis.nasa.gov/",
        "cloud-providers": ["LAADS"],
        "on-prem-providers": ["LAADS"],
        "s3-credentials": "https://data.laadsdaac.earthdatacloud.nasa.gov/s3credentials",
        "eulas": [],
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
    "LAADS",
]

# Some testing urls behind EDL
DAAC_TEST_URLS = [
    (
        "https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-protected/"
        "JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/"
    ),
    (
        "https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/ATLAS/"
        "ATL03/005/2018/10/14/dummy.nc"
    ),
    (
        "https://n5eil01u.ecs.nsidc.org/DP7/ATLAS/ATL06.005/2018.10.14/"
        "ATL06_20181014045341_02380102_005_01.iso.xml"
    ),
    ("https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH10_M.2.0/1948/"),
    (
        "https://e4ftl01.cr.usgs.gov//DP114/MOTA/MCD43A3.006/2000.02.24/"
        "MCD43A3.A2000055.h15v07.006.2016101151720.hdf.xml"
    ),
    "https://daac.ornl.gov/daacdata/npp/grassland/NPP_BCN/data/bcn_cli.txt",
]


def find_provider(
    daac_short_name: Optional[str] = None, cloud_hosted: Optional[bool] = None
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


def find_provider_by_shortname(short_name: str, cloud_hosted: bool) -> Union[str, None]:
    base_url = "https://cmr.earthdata.nasa.gov/search/collections.umm_json?"
    providers = requests.get(
        f"{base_url}&cloud_hosted={cloud_hosted}&short_name={short_name}"
    ).json()
    if int(providers["hits"]) > 0:
        return providers["items"][0]["meta"]["provider-id"]
    else:
        return None
