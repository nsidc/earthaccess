## Search for granules within a collection using spatial and temporal filters 

Import the DataGranules class
```py
from earthaccess import DataGranules
```

Search for granules within a data set. You need to know the short name which can be found on the data set landing page
```py
Query = DataGranules().short_name("ATL03").temporal("2022-05-01",2022-05-31").bounding_box(-53.4,69.6,-50.8,72.0)
```

Print the number of granules found

```py
print(f"Granules found: {Query.hits()}")
```

