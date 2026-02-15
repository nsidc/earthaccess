Import earthaccess library and search for granules within a data set using spatial and temporal filters. You need to know the short name of the data set which can be found on the data set landing page.

```py
import earthaccess

results = earthaccess.search_data(
    short_name = "ATL06",
    version = "005",
    cloud_hosted = True,
    bounding_box = (-10,20,10,50),
    temporal = ("2020-02", "2020-03"),
    count = 100
)
```

### **Searching for data**

Once we have selected our dataset we can search for the data granules using *doi*, *short_name* or *concept_id*.
If we are not sure or we don't know how to search for a particular dataset, we can start with the [NASA Earthdata Search portal](https://search.earthdata.nasa.gov/). For a complete list of search parameters we can use visit the extended [API documentation](https://earthaccess.readthedocs.io/en/latest/user-reference/api/api/).

```python

results = earthaccess.search_data(
    short_name='SEA_SURFACE_HEIGHT_ALT_GRIDS_L4_2SATS_5DAY_6THDEG_V_JPL2205',
    cloud_hosted=True,
    bounding_box=(-10, 20, 10, 50),
    temporal=("1999-02", "2019-03"),
    count=10
)


```

Now that we have our results we can do multiple things: We can iterate over them to get HTTP (or S3) links, we can download the files to a local folder, or we can open these files and stream their content directly to other libraries e.g. xarray.
