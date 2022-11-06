# **earthaccess** 🌍
A Python library to search and access NASA datasets

<p align="center">

<a href="https://pypi.org/project/earthdata" target="_blank">
    <img src="https://img.shields.io/pypi/v/earthdata?color=%2334D058&label=pypi%20package" alt="Package version">
</a>

<a href="https://pypi.org/project/earthdata/" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/earthdata.svg" alt="Python Versions">
</a>

<a href="https://github.com/psf/black" target="_blank">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
</a>

<a href="https://nsidc.github.io/earthdata/" target="_blank">
    <img src="https://readthedocs.org/projects/earthdata/badge/?version=latest&style=plastic" alt="Documentation link">
</a>

</p>


## Overview


The real power of open science in the age of cloud computing is only unleashed to its full potential if we have easy-to-use workflows that facilitate working with data in an inclusive, efficient and reproducible way. Unfortunately —as it stands today— scientists are facing a steep learning curve for unintended complex systems and end up spending more time on the technicalities of the cloud and NASA APIs rather than focusing on their important science.

During several workshops organized by [NASA Openscapes](https://nasa-openscapes.github.io/events.html) the need to provide easy-to-use tools to our users became evident. We shouldn’t need to be cloud infrastructure engineers to easily work with the data if it’s hosted on a S3 bucket. This was the main reason behind *earthaccess*, a Python library that aims to simplify our workflows to address some of the pain points of programmatic access to NASA datasets within the PyData ecosystem.

With *earthaccess* we can login with NASA, search and download data with a few lines of code and even more relevant, our code will work the same way if we are running it in the cloud or from our laptop. ***earthaccess*** handles authentication with [NASA's Earthdata Login (EDL)](https://urs.earthdata.nasa.gov), search using NASA's [CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html) and access through [`fsspec`](https://github.com/fsspec/filesystem_spec). If all of this sounds like gibberish... no worries we are here to help! Please ask us anything on [project board!](https://github.com/nsidc/earthdata/discussions).

The only requirement to use this library is to open a free account with NASA [EDL](https://urs.earthdata.nasa.gov).





> **⚠️ Warning ⚠️**: The project has recently been renamed from earthdata to earthaccess. If your environment depends on earthdata, please update your reference to earthaccess v0.5.0



<a href="https://urs.earthdata.nasa.gov"><img src="https://auth.ops.maap-project.org/cas/images/urs-logo.png" /></a>

<img src="https://user-images.githubusercontent.com/717735/199083271-79ce5113-b680-4fe5-a1bf-6c927bf02c75.jpg" />

## Installing earthaccess

Install the latest release using conda

```bash
conda install -c conda-forge earthaccess
```

Using Pip

```bash
pip install earthaccess
```

Try it in your browser without installing anything! [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nsidc/earthdata/main)

## Do where do we start?

Data Pathfinders guide users through the process of selecting application-specific datasets and learning how to use them through intuitive tools, facilitating equal and open access to the breadth of NASA Earth science data. The pathfinders are intended to familiarize users with and provide direct links to the applicable, commonly-used datasets across NASA’s Earth science data collections. After getting started here, there are numerous NASA resources that can help develop one’s skills further.

[https://www.earthdata.nasa.gov/learn/pathfinders](
https://www.earthdata.nasa.gov/learn/pathfinders)

## Authentication

After we get a new account with EDL we can authenticate ourselves using 3 different methods:

1. Using a `.netrc` file
    * We can use *earthaccess* to read our credentials fom a netrc file
2. Reading our credentials from environment variables
    * if available we can use environment variables **EDL_USERNAME** and **EDL_PASSWORD**
3. Interactively entering our credentials
    * We can ask for these credentials and even persist them to a `.netrc` file

```python
import earthaccess

auth = earthaccess.login(strategy="netrc")
if not auth:
    auth = earthaccess.login(strategy="interactive", persist=True)
 ```

Once we are authenticated with NASA EDL we can:

* Get a file from a DAAC using a `fsspec` session.
* Requests temporary S3 credentials from a particular DAAC.
* Use the library to download or stream data directly from S3.
* Regenerate CMR tokens (used for restricted datasets)


## Searching for data

Once we have selected our dataset we can search for the data granules using *doi*, *short_name* or *concept_id*.
If are not sure or we don't know ohw to search for a particular dataset we can start with the "searching for data" tutorial or through the data pathfinder program listed above. For a complete list of search parameters we can use visit the API extended documentation.

```python

query = earthaccess.search_data(
    short_name='ATL06',
    version="005",
    cloud_hosted=True,
    bounding_box=(-10, 20, 10, 50),
    temporal=("2020-02", "2020-03")
)

print(f"Granules found: {query.hits()}")

# We execute our query and ask for 10 results only
results = query.get(10)

# If we want all the results we can iterate over items() 
# for results in query.items():
#     print(len(results))
#     some cool stuff

```

Now that we have our results we can do multiple things, we can iterate over them to get HTTP (or S3) links; we can download the files to a local folder or we can open these files and stream their content directly to other libraries e.g. xarray.

## Accessing the data

### Option 1: we only want the links

If we already have a workflow in place for downloading our data, we can use *earthaccess* as a search-only library and get HTTP links from our query results. This could be the case if our current workflow uses a different language and we only need the links as input.

```python

# if the dataset is cloud hosted there will be S3 links available, the access parameter accepts direct or external, direct access is only possible if we are in us-west-2
data_links = [granule.data_links(access="direct") for granule in results]

# or if the data is an on-prem dataset
data_links = [granule.data_links(access="external") for granule in results]

```

> Note: as a bonus, *earthaccess* can get S3 credentials for us, or auhenticated HTTP sessions in case we want to use them with a different library.

### Option 2: we want to download the results to a local folder

This option is practical if we have the necessary space available on disk, the library will inform us about the approximate size to be downloaded and its progress.
```python
for results in query.items():
    # results is a list of up to 2000 granules (files)
    earthaccess.download(results,
                         local_path="./data/atl06/",
                         auth=auth)

```

### Option 3: we want to stream the results directly to xarray

This method works better for in-region access when we are working with gridded datasets (processing level 3 and above).

```python
import xarray as xr

ds = xr.open_mfdataset(earthaccess.open(results, auth=auth), engine="scipy")

```
And that's it! this code works the same for cloud hosted data and we don't have to change it if we are using DAAC hosted datasets.

## More examples:

* earthaccess search capabilities (searching for services and variables)
* renovating EDL access tokens with 1 line of code
* earthaccess and other client libraries (py-STAC, PyDAP, Harmony)
* Searching for cloud hosted collections
* Searching for collections under an access control list (early users)
* Printing relevant information from a collection
* Visualizing data granules
* Getting S3 credentials from the DAACs
* Direct access with S3FS session for cloud hosted collections

### Compatibility

Only **Python 3.8+** is supported.

## Code of Conduct

See [Code of Conduct](CODE_OF_CONDUCT.md)

## Level of Support

* This repository is not actively supported by NSIDC but we welcome issue submissions and pull requests in order to foster community contribution.

<img src="https://raw.githubusercontent.com/nsidc/earthdata/main/docs/nsidc-logo.png" width="84px" />

## Glossary

## Contributors

[![Contributors](https://contrib.rocks/image?repo=nsidc/earthdata)](https://github.com/nsidc/earthdata/graphs/contributors)

## Contributing Guide

Welcome! 😊👋

> Please see the [Contributing Guide](CONTRIBUTING.md).
