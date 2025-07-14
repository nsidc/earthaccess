# Status

Earthaccess relies on the Common Metadata Repository (CMR) API and Earthdata Login (EDL) service to provide functionality. You can check the status of these NASA Earthdata services manually or programmatically.

## Manual Status Check

You can check the status of NASA Earthdata services manually for [PROD](https://status.earthdata.nasa.gov/) and [UAT](https://status.uat.earthdata.nasa.gov/) systems.

## Programmatic Status Check

You can check the status of Earthdata services  programmatically this way.

```py
import earthaccess

nasa_status = earthaccess.status()

if any(service_status != 'OK' for service_status in nasa_status.values()):
   raise Exception("NASA APIs unavailable, please try again later.")
```
