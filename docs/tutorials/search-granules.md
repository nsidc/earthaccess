## Search for granules within a collection using spatial and temporal filters 

Import earthaccess library and search for granules within a data set. You need to know the short name which can be found on the data set landing page. 

```py
import earthaccess

results = earthaccess.search_data(
    short_name = "ATL06",
    version = "005"'
    cloud_hosted = True, 
    bounding_box = (-10,20,10,50),
    temporal = ("2020-02", "2020-03"),
    count = 100
)
```

