# Status

Earthaccess relies on the Common Metadata Repository (CMR) API and Earthdata Login (EDL) service to provide functionality. You can check the status of these NASA Earthdata services manually or programmatically.

## Manual Status Check

You can check the status of NASA Earthdata services manually for [PROD](https://status.earthdata.nasa.gov/) and [UAT](https://status.uat.earthdata.nasa.gov/) systems.

## Programmatic Status Check

You can check the status of Earthdata services  programmatically this way.

```py
import earthaccess

# Equivalent to earthaccess.status(system=PROD, raise_on_outage=False)
nasa_status = earthaccess.status()
print(nasa_status)
```
