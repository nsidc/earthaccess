# How to search for services using `earthaccess`

You can search for services associated with a dataset.  Services include a
back-end processing workflow that transforms or processes the data in some way
(e.g.  clipping to a spatial extent or converting to a different file format).

`earthaccess` facilitates the retrieval of service metadata via the
`search_datasets` function.  The results from the `search_datasets` method are
an enhanced Python dictionary that includes a `services` method which returns
the metadata for all services associated with a collection.  The service results
are returned as a Python dictionary.

To search for services, import the earthaccess library and search by dataset
(you need to know the short name of the dataset which can be found on the
dataset landing page):

```py
import earthaccess

datasets = earthaccess.search_datasets(
    short_name="MUR-JPL-L4-GLOB-v4.1",
    cloud_hosted=True,
    temporal=("2024-02-27T00:00:00Z", "2024-02-29T23:59:59Z"),
)
```

Parse the service results to return metadata on services available for the dataset.

```py
for dataset in datasets:
    print(dataset.services())
```

Alternatively, you may search directly for services.  For example:

```py
services = earthaccess.search_services(provider="POCLOUD", keyword="COG")
```

The keyword arguments supported by the `search_services` function are
constrained to what the NASA CMR allows, as described in the
[Service section of the CMR API](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#service).
