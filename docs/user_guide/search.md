# Search

!!! note "This Page is a Work in Progress"

    We are reorganizing and updating the documentation, so not all pages are complete.  If you are looking for information about authenticating using earthaccess see the
    How-Tos and Tutorials in links below.

    * [Quick start](../quick-start.md)
    * [How-To Access Data](../howto/access-data.md)

`earthaccess` enables users to search for datasets (what NASA call's collections) and the data within those datasets (what NASA calls granules).

!!! note "Collections and Granules"

    A collection is a set of data products or files for the same release of that product,
    data generated during an experiment or campaign.

    A granule is the smallest aggregation of data.  It could be an individual scene or swath acquired
    at a given timestep.  You can think of granules as files.

To search for collections or datasets use `search_datasets`.  To search for individual files use `search_data`.

`search_datasets` and `search_data` have a common set of search parameters, as well as some parameters that are only available to `search_datasets` and `search_data`.  See the table of search parameters below to see common and unique parameter keywords.


## Search for datasets using `search_datasets`

Show basic search

search by shortname and time range

spatial searches bounding-box, point, polygon, circle, line - separate section


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

## `search_services`

_Add table showing which methods are available for search_datasets and search_data_

| Query | `search_datasets` | `search_data` |
|-------|-------------------|---------------|
| concept_id | | |
| temporal | | |
| bounding_box | | |
| polygon | | |
| point | | |
| circle | | |
| line | | |
| keyword | | |
| doi | | |
| short_name | | |
| cloud_hosted | | |
| version | | |
| instrument | | |
| project | | |
| provider | | |
| daac | | |
| data_center | | |
| has_granules | | |
| orbit_number | | |
| day_night_flag | | |
| cloud_cover | | |

