# Search

!!! note "This Page is a Work in Progress"

    We are reorganizing and updating the documentation, so not all pages are complete.  If you are looking for information about authenticating using earthaccess see the
    How-Tos and Tutorials in links below.

    * [Quick start](../quick-start.md)
    * [How-To Access Data](../howto/access-data.md)

`earthaccess` enables users to search for datasets (what NASA call's collections), the data within those datasets (what NASA calls granules), and the services that are available for a given dataset.

!!! note "Collections and Granules"

    A _collection_ is a set of data products or files for the same release of that product,
    data generated during an experiment or campaign.

    A _granule_ is the smallest aggregation of data.  It could be an individual scene or swath acquired
    at a given timestep.  You can think of granules as files.

To search for collections or datasets use `search_datasets`.  To search for individual files use `search_data`.  To search for services use `search_services`

`search_datasets` and `search_data` have a common set of search parameters, as well as some parameters that are only available to `search_datasets` and `search_data`.  See the table of search parameters below to see common and unique parameter keywords.


## Search for datasets using `search_datasets`

#### A basic search

`search_datasets` allows datasets to be searched using combinations of keywords.  Here, we use the `platform` keyword to search for all datasets matching `icesat-2`.

```
results = earthaccess.search_datasets(
    platform="icesat-2"
    )
```

`search_datasets` returns a Python list of results.  We can find the number of dataets using the built-in Python `len()` function.

```
print(len(result))
```
```
82
```

The number of datasets returned can be refined by using additional keywords.  Here, we use `cloud_hosted` and `downloadable` to restrict datasets returned to only those that can be downloaded from the AWS-hosted NASA Earthdata Cloud.

!!! note "NASA Earthdata Cloud"

    By July 2026, all NASA data will be hosted in the cloud.  _What is the plan for archiving both ECS and V0 - will **all** data be in the cloud, will some data be discoverable but not downloadable._

```
results = earthaccess.search_datasets(
    platform="icesat-2",
    downloadable=True,
    cloud_hosted=True,
    )
print(len(results))
```
```
59
```

This refined search now returns 59 datasets.

Each element of the `results` list is a `earthaccess.results.DataCollection` object.  This is a custom dictionary with methods to return a dataset `summary`, `concept_id`, `data_type`, `version`, `abstract`, `land_page`, urls to data links - `get_data`, information about the S3 bucket containing the data granules - `s3_bucket`, a list of services available for the dataset `services`, and a method to return specific fields within the dictionary `get_umm`.  This last method requires some knowledge of the NASA [Unified Metadata Model (UMM)](https://www.earthdata.nasa.gov/about/esdis/eosdis/cmr/umm).

```
# Add code for getting summary etc
pprint(result[0].summary())
```
```
{
    'short-name': 'ATL07',
    'concept-id': 'C2564625052-NSIDC_ECS',
    'version': '006',
    'file-type': "[{'FormatType': 'Native', 'Format': 'HDF5', 'FormatDescription': 'HTTPS'}]",
    'get-data': [
        'https://n5eil01u.ecs.nsidc.org/ATLAS/ATL07.006/',
        'https://search.earthdata.nasa.gov/search?q=ATL07+V006',
        'https://nsidc.org/data/data-access-tool/ATL07/versions/6/'
        ]
}
```

_Maybe add some code to get structure of dict_

#### Search by time range


#### Perform Spatial Search
spatial searches bounding-box, point, polygon, circle, line - separate section

#### Search by provider or data archive



search by shortname and time range




Services
This is a really big object
```
In [24]: result[0].services()
```

S3 bucket
Currently empty or is it because not cloud-hosted
```
result[0].s3_bucket()
```

cloud_hosted
```
result[0].cloud_hosted
```

landing page is empty for example
```
In [24]: result[0].landing_page()
```

Data type
```
In [24]: result[0].data_type()
Out[24]: "[{'FormatType': 'Native', 'Format': 'HDF5', 'FormatDescription': 'HTTPS'}]"
```

Abstract
```
result[0].abstract()
```

### Parameters

- concept_id - filter by concept-id 
- keyword - case insensitive and wildcard search through "over two dozen" fields in CMR 
- doi - search datasets by doi
- instrument - search datasets by instrument name - not all datasets have an instrument name
- project - search datasets by associated project
- short_name
- temporal - from and to can be string, date or datetime object
- cloud_hosted - only match granules hosted in the cloud
- provider - NASA datacenter of DAAC - list these
- data_center - alias of daac method
- daac match collections to DAAC
- version  
- fields allows masking of reponse to just specified fields
- has_granules - match only collections with granules
- hits
- count - just get up to count granules

returns a list of data collections/datasets

## `search_data`

- orbit_number
- day_night_flag
- cloud_cover
- platform (is this available for collections)
- granule_name

### Search by granule name


### Search by granule name using wild cards

```
granules = earthaccess.search_data(
    short_name="ATL07",
    temporal=("2022-07-26","2022-07-26"),
    granule_name="ATL07-01_*_0531????_*_*.h5",
    version="006",
)
```

## `search_services`

## Available arguments for search methods

| Query | `search_datasets` | `search_data` | `search_services` |
|-------|-------------------|---------------|-------------------|
| concept_id | x | | |
| temporal | x | | |
| bounding_box | x | | |
| polygon | x | | |
| point | x | | |
| circle | x | | |
| line | x | | |
| keyword | x | | |
| doi | x | | |
| short_name | x | | |
| cloud_hosted | x | | |
| version | x | | |
| instrument | x | | |
| project | x | | |
| provider | x | | |
| daac | x | | |
| data_center | x | | |
| has_granules | x | | |
| orbit_number | | | |
| day_night_flag | | | |
| cloud_cover | | | |

