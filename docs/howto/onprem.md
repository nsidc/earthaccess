# Download data for on-prem datasets

Import the `earthaccess` library, search for granules in an on-prem dataset and download to a local computer.
The Sea Ice Concentrations from Nimbus-7 SMMR and DMSP SSM/I-SSMIS Passive Microwave Data, Version 2, dataset is used.
This has the shortname NSIDC-0051.  We search for and download data granules for the northern hemisphere for November 2023.
In this example, granules are downloaded to the current working directory using the `local_path` keyword.  This can be changed to your preferred download location.

```py
import earthaccess

auth = earthaccess.login()

results = earthaccess.search_data(
    short_name='NSIDC-0051',
    temporal=('2022-11-01', '2022-11-30'),
    bounding_box=(-180, 0, 180, 90)
)

downloaded_files = earthaccess.download(
    results,
    local_path='.',
)
```
