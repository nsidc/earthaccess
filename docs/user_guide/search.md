# Search

## Overview

Searching for NASA Earthdata is the core function is `earthaccess`.  NASA organizes Earthdata into [_collections_](<link-to-glossary>).  An example of a collection is the [MODIS/TERRA Global Daily Snow Cover](https://nsidc.org/data/mod10a1/versions/61).  You can think of a collection as a dataset.  Collections contain many data _granules_, each granule is a file.  For the MODIS snow cover data, each granule (or file) contains data for one day for a 10&deg; x 10&deg; area of the globe.

Using `earthaccess`, you can search for datasets using [`search_datasets`](#search-for-datasets-using-search_datasets) or search for files (or granules) within a dataset using [`search_data`](#search-for-data-granules-using-search_data).  For example, you may want snow cover data or perhaps data for ocean color but not know a specific dataset that contains this data.  `search_datasets` allows you to search by keywords.  Or you may want data about canopy height in the Amazon rain forest for a given date but do not know what datasets are available for this region of time range.  `search_datasets` allows you to define a region of interest and a time range of interest to your search.  Alternatively, you might know you want to work with data from the MODIS snow cover dataset, in the example above, but want to find out which version of that data is available.

On the other hand, you may know which dataset you want to work with but need to find the data files for a time period and region of interest.  You can find these files with `search_data`.  You might want to further refine that search to find only files with less than 50% cloud cover or with data collected during day-time.  `search_data` accepts these search terms as well.

NASA also offers a number of services to subset and transform data.  These services are not available for datasets.  You can use `search_services` to discover which datasets have particular services.

`search_datasets` and `search_data` have some search parameters in common, as well as some parameters that are only available to `search_datasets` and `search_data`.  Below, we first cover some basic searches using `search_datasets` and `search_data`.  We then give some more examples and detail on keywords common to both functions.


## Search for datasets using `search_datasets`

### A basic search

[`search_datasets`](../user-reference/api/api.md/#earthaccess.api.search_datasets) allows you to search for NASA datasets using combinations of keywords.  As a simple example, we use the `keyword` keyword to search for all datasets matching `icesat-2`.

```python
results = earthaccess.search_datasets(
    keyword="icesat-2"
    )
```

`search_datasets` returns a Python list of results.  We can find the number of datasets using the built-in Python `len()` function.  If there are no matches for the search, the list is empty with length 0.

```python
print(len(result))
```
```
82
```

!!! note "Migrating NASA Earthdata to the Cloud"

    NASA is in the process of migrating datasets from on-premises archives to the cloud.  By July 2026, all NASA data will be hosted in the cloud.  During migration, as datasets are moved, access to on-premises archives is being removed.  This may cause you to have counts of results different from counts here.

### Refine the search by adding more keywords

The number of datasets returned can be refined by using additional keywords.  For a full list of keywords accepted by `search_datasets` see the [User Reference](../user-reference/api/api.md/#earthaccess.api.search_datasets).  Here, we use `cloud_hosted` and `downloadable` to restrict datasets returned to only those that can be downloaded from the AWS-hosted NASA Earthdata Cloud.

```python
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

#### Search by provider or data archive

You might know that a particular DAAC has a dataset or just datasets for a given variable, for example snow.  Here, we use the `daac` or `provider` keywords to find all the datasets at NSIDC DAAC, the National Snow and Ice Data Center.

```python
results = earthaccess.search_datasets(
    daac="nsidc",
    )
```

#### Search by version

In general, DAACs archive the two most recent versions of a dataset.  You might want to find the **concept-id**, the unique identifier for a dataset for that version.  Here, we search for the concept-id for version 007 of ICESat-2 Geolocated Photon Heights (ATL03).

```python
results = earthaccess.search_datasets(
    short_name="ATL03",
    version="007",
    )
```

```python
len(results)
```

```
1
```

The concept-id can be accessed directly using the `concept_id` method.

```
results[0].concept_id()
```
```
'C3326974349-NSIDC_CPRD'
```


### Accessing and understanding the search results

Each element of the `results` list is a `earthaccess.results.DataCollection` object.  A summary showing key fields for each result in `results` can be displayed using the `summary` method.  Each result in `results` is accessed in the same way you access elements in a Python list; by giving an index.

```python
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

The `summary` method returns the **short-name** for the dataset; the **concept-id**, a unique identifier for the dataset; the dataset **version**; the **file-type** of the files in the dataset; and a set of links to access the data files.

!!!note "You need to login to use the **get-data** links"

    You can search for datasets and data without logging in to NASA's Earthdata Login but you must login before you download data.  `earthaccess` makes this easy with the `login` method.  See the [Authentication section](./authenticate.md) for more information.

In addition to the `summary` method, there are methods to return the dataset [`concept_id`](<link-to-glossary-entry>), `data_type`, `version`, the dataset `abstract`, the url for the dataset `landing_page`, urls for data links - `get_data`, information about the S3 bucket containing the data granules - `s3_bucket`, and a list of services available for the dataset `services`.

The `concept_id` is one way to search for granules in a dataset using `search_data`.

```python
print(results[0].concept_id)
```
```
'C2564625052-NSIDC_ECS'
```


## Search for data granules using `search_data`

### A simple example

Once you know which dataset you want to use, you can use `search_data` to find data files to work with.  NASA Earthdata archives contain 1000's of datasets and files.  The preserve computational resources you can only search a subset of datasets, so you must provide a **concept-id**, **provider**, **short-name** or **version** to `search_datasets` to limit the search.  Even then, large searches can take a long time, so it is best to further refine your search using a time range or region of interest.  `search_datasets` also allows you to request a given number of datasets using the `count` parameter.  This is useful is you want to find a small number data files so you can explore the data before downloading a large number of files.

In this example, we use dataset `short_name`, `version` and `count` to find land ice heights from the ICESat-2 laser altimeter.  The `short_name` for this dataset is **ATL06**.

```python
results = earthaccess.search_data(
    short_name="ATL06",
    version="007",
    count=10,
    )
```

```python
len(results)
```

```
10
```

Because we requested only the first 10 results, we only get 10 results.

### Refining the search

Searches can be refined further by `orbit_number`, cloud cover fraction and day-night flag.

!!!warning "Not all datasets have metadata to use these keywords"

    Not all datasets have the relevant metadata to allow all keywords to be used.  If the metadata relevant to a keyword is not included in the dataset metadata record, a search will return zero results.  One strategy is to start with a broard search, for example just `short_name` or `concept_id`, for a dataset but set the `count` argument to a small number, e.g. 10.  Then add keywords to see if you continue to get results.  If you continue to get 10 results with a new keyword, it is likely that the keyword is valid.

Orbit number is a way to track the number of passes a satellite platform has made.  You can think of it as a proxy for time since launch.

```python
results = earthaccess.search_data(
    short_name="ALT10",
    version="007",
    orbit_number=436,
    )
```

```python
len(results)
```

```
4
```

For datasets with data in visible wavelengths, cloud cover can be a problem.  For most analyses, users want data with little or no clouds.  The `cloud_cover` can be used to filter results to return images with cloud cover less than or between certain ranges.  Cloud cover is takes a Python tuple containing a minimum and maximum cloud cover fraction.

In this example we search for data from the Harmonized-Landsat-Sentinel Sentinel-2 Multi-spectral Instrument Surface Reflectance Daily Global 30m v2.0 (concept-id: C2021957295-LPCLOUD) with less than 50% cloud cover.  Here, we limit results to the first 10 granules found.  Without the cloud cover filter, a full search returns 111,006 granules.  With the cloud cover filter, the search returns 63,114.

```python
results = earthaccess.search_data(
    concept_id="C2021957295-LPCLOUD",
    cloud_cover=(0,50),
    count=10
    )
```

Filtering for only day-time granules is another useful filter.  This can be done with the `day_night_flag`.  `day_night_flag` accepts `day`, `night` and `unspecified`.

!!!warning "Not all datasets use these flags"

    Some datasets have "both" as a value for the day-night metadata.  This is not a valid input for CMR and will raise an error.

In this example, we search for daytime granules in the MODIS/Terra Global Daily Snow Cover dataset (MOD10A1).

```python
results = earthaccess.search_data(
    short_name="MOD10A1",
    day_night_flag="day",
    count=10,
    )
```

The MODIS data is a big dataset.  The dataset contain 2,814,982 granules.  With `day_night_flag="day"`, a full search would return 2,465,185 granules.

### Search by Granule name

`search_data` allows for searches by granule name.  This is useful if you know which granule you want.  For example, a particular granule is used in a paper and you want to reproduce the analysis.

Here, we search for a particular granule from the ICESat-2 Sea Ice Freeboard dataset (ATL10).

```python
results = earthaccess.search_data(
    short_name="ATL10",
    granule_name="ATL10-02_20181014000347_02350101_006_02.h5",
    )
```

The `granule_name` keyword accepts strings with wildcard characters `*?`, with `*` matching zero or more characters and `?` matching any single character.  Filenames for granules usually encode date and some form of geolocation information.  For example, MODIS granules are organized into a grid of tiles that are referenced by horizontal (`h`) and vertical (`v`) indices, e.g.

MOD10A1.A2025252.**h08v07**.061.2025254175256.hdf

ICESat-2 products are organized by Reference Ground Track (RGT) and cycles.  A RGT is an imaginary line Earth surface traced by the satellite.  There are 1,387 RGTs.  Each RGT repeated every 91 days as the satellite orbits Earth.  Cycles count the 91-day periods.  RGT and cycle numbers are encoded as 4-digit and 2-digit numbers in ICESat-2 product file names, e.g.

ATL10-02_20181014000347_**023501**01_006_02.h5

Dataset user guides contain information about filename formats.

We can use wildcard characters to construct a filename string to search for a particular set of granules.  Below, modify the last example to search for all ICESat-2 ATL10 granules that follow RGT 235 by relacing the date-time stamp in the filename with `*`.

```python
results = earthaccess.search_data(
    short_name="ATL10",
    granule_name="ATL10-02_*_0235????_006_02.h5",
    )
len(results)
```

```
9
```

This search matches 9 granules.


## Search for datasets or data by time range

The `temporal` keywords can be used with `search_dataset` or `search_data` to find collections
of granules within a given time range.  A time range is passed to `temporal` as a two element Python tuple giving the beginning datetime and ending datetime of the search.  Datetime can be passed as a [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) formatted string or as a Python datetime-like object.

Date strings can be full date-time strings, for example 2025-09-07 16:00:00 or 2025-09-07T16:00:00.  Or a truncated string with just year, month and day, for example 2025-09-07.

```python
results = earthaccess.search_data(
    short_name="ATL06",
    temporal=("2025-01-01","2025-01-15"),
    )
```

Python `datetime` objects can also be passed to `temporal`.  This is especially useful if you are trying to automate searches and store dates as `datetime` objects.

```python
import datetime

results = earthaccess.search_data(
    short_name="ATL06",
    temporal=(
        datetime.datetime(2025,1,1),
        datetime.datetime(2025,1,15)
        ),
    )
```

## Search for datasets or data using a region of interest

Both `search_datasets` and `search_data` accept several keywords to search by a region of interest.  CMR also accepts Shapefiles and GeoJSON files but these options are not currently available in `earthaccess`.

All the methods described here require coordinates to be in geodetic coordinates, e.g. longitude and latitude, expressed as decimal degrees.

In each case, matching granules or datasets are returned if their geometries intersect with the geometries passed to `earthaccess`.

### Bounding box

A bounding box is defined by lower left longitude, lower left latitude, upper right longitude, upper right latitude.  This is passed to the `bounding_box` keywords as a Python tuple of floats.

```
results = earthaccess.search_data(
    short_name="ATL06",
    bounding_box=(-46.5, 61.0, -42.5, 63.0),
    )
```

### Polygon

A polygon is defined as a list of tuples containing longitude and latitude points.  The last point in the sequence must match the first point in the sequence. For example:

```
[(lon0, lat0), (lon1, lat1), (lon2, lat2),... , (lonN, latN), (lon0, lat0)]
```

Polygon points must be in counter-clockwise order.


The following example searches for ICESat-2 land ice heights (ATL06) over the Jakobshavn Isbrae in Greenland.

```python
polygon = [
    (-49.64860422604741, 69.23553485026147),
    (-49.667876114626296, 69.07309059285959),
    (-49.1722491331669, 69.03175841820749),
    (-47.53552489113113, 69.03872918462292),
    (-47.35616491854395, 69.22149993224824),
    (-48.1447695277283, 69.33507802083219),
    (-49.178671242118384, 69.29455117736225),
    (-49.64860422604741, 69.23553485026147),
]

results = earthaccess.search_data(
    short_name="ATL06",
    polygon=polygon,
    )
```

You can use tools such as [geojson.io](https://geojson.io/) to draw polygons and return a GeoJSON file.  Or use a GIS package to create a Shapefile.  The Geopandas Python package can be used to read these files and convert then to the correct format for `earthaccess`.  For example.

```python
import geopandas

gdf = geopandas.read_file(<my_shapefile_or_geojson_file>)

my_polygon = [(lon,lat) for lon, lat in zip(*gdf.loc[0].geometry.exterior.xy)]
```

### Point

A point is defined as a tuple containing a longitude and latitude.

```python
lon, lat = (-105.25303896425012, 40.01259873086735)

results = earthaccess.search_data(
    short_name="ATL06",
    point=(lon,lat),
    )
```

### Circle

A circle is defined as a longitude, latitude pair and a radius in meters.  Here, we extend the point in the example above to find granules within 1 km of the point (-105.253,40.012).

```python
lon, lat = (-105.25303896425012, 40.01259873086735)
radius = 1000.

results = earthaccess.search_data(
    short_name="ATL06",
    circle=(lon,lat, radius),
    )
```

### Line

A line is a Python list of tuples containing longitude-latitude pairs.

In this example we search for ICESat-2 Geolocated photon height (ATL03) tracks that intersect with the [Canyon de Chelly](https://www.nps.gov/cach/index.htm), AZ (Near Chinle, [Naabeehó Bináhásdzo](https://en.wikipedia.org/wiki/Navajo_Nation)).

```python
line = [
    (-109.49099495904196, 36.141620186146454),
    (-109.46326273316441, 36.12549319389707),
    (-109.42416829289516, 36.11336807764218),
    (-109.39942951589708, 36.10816134722084),
    (-109.33995221922424, 36.10943400693182),
    (-109.28600071040317, 36.11941578661717),
]

results = earthaccess.search_data(
    short_name="ATL03",
    line=line,
    )
```

## Search for services

NASA Earthdata provides services that you can use to transform data before you download it.  Transformations include converting data files to a different file format, subsetting data by spatial extent, time range or variable, reprojecting or transforming data to a different coordinate reference system (CRS) from the one it is stored in.  Not all datasets have services and not all transformation services are available for a given dataset.

There are wo ways to discover which services are available for a dataset.  One way is to call the `services` method on a result returned by `search_datasets`.  See the [Results] section of this User Guide for more information.

```python
results = earthaccess.search_datasets(
    short_name="MUR-JPL-L4-GLOB-v4.1",
    cloud_hosted=True,
    temporal=("2024-02-27T00:00:00Z", "2024-02-29T23:59:59Z"),
    )
```

```python
for dataset in datasets:
    print(dataset.services())
```

The other way to use the `search_services` function.  This takes the following keywords:

- `provider`: the name of the DAAC, e.g. `"PODAAC"`
- `concept_id`: the concept ID of the service, e.g. `"S3084748458-POCLOUD"` (starts with a "S")
- `name`: the name of the service, e.g. `"PODAAC_SWODLR"`
- `native_id`: an alternative name of the service, e.g `"POCLOUD_podaac_swodlr"`

```
services = earthaccess.search_services(provider="PODAAC")
```

`search_services` returns a list of Python doctionaries.
