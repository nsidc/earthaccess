<p align="center">
<img alt="earthaccess, a python library to search, download or stream NASA Earth science data with just a few lines of code" src="https://user-images.githubusercontent.com/717735/205517116-7a5d0f41-7acc-441e-94ba-2e541bfb7fc8.png" width="70%" align="center" />
</p>

<p align="center">

<a href="https://zenodo.org/badge/latestdoi/399867529" target="_blank">
    <img src="https://zenodo.org/badge/399867529.svg" alt="DOI" />
</a>

<a href="https://twitter.com/allison_horst" target="_blank">
    <img src="https://img.shields.io/badge/Art%20By-Allison%20Horst-blue" alt="Art Designer: Allison Horst">
</a>

<a href="https://pypi.org/project/earthaccess" target="_blank">
    <img src="https://img.shields.io/pypi/v/earthaccess?color=%2334D058&label=pypi%20package" alt="Package version">
</a>

<a href="https://anaconda.org/conda-forge/earthaccess" target="_blank">
    <img src="https://img.shields.io/conda/vn/conda-forge/earthaccess.svg" alt="Conda Versions">
</a>

<a href="https://pypi.org/project/earthaccess/" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/earthaccess.svg" alt="Python Versions">
</a>

<a href='https://earthaccess.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/earthaccess/badge/?version=latest' alt='Documentation Status' />
</a>

</p>

## **Overview**

*earthaccess* is a **python library to search, download or stream NASA Earth science data** with just a few lines of code.


In the age of cloud computing, the power of open science only reaches its full potential if we have easy-to-use workflows that facilitate research in an inclusive, efficient and reproducible way. Unfortunately —as it stands today— scientists and students alike face a steep learning curve adapting to systems that have grown too complex and end up spending more time on the technicalities of the tools, cloud and NASA APIs than focusing on their important science.

During several workshops organized by [NASA Openscapes](https://nasa-openscapes.github.io/events.html), the need to provide easy-to-use tools to our users became evident. Open science is a collaborative effort; it involves people from different technical backgrounds, and the data analysis to solve the pressing problems we face cannot be limited by the complexity of the underlying systems. Therefore, providing easy access to NASA Earthdata regardless of the data storage location (hosted within or outside of the cloud) is the main motivation behind this Python library.

## **Installing earthaccess**

You will need Python 3.8 or higher installed.

Install the latest release using conda

```bash
conda install -c conda-forge earthaccess
```

Using Pip

```bash
pip install earthaccess
```

Try it in your browser without installing anything! [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nsidc/earthaccess/main)


## **Usage**


With *earthaccess* we can login, search and download data with a few lines of code and even more relevant, our code will work the same way if we are running it in the cloud or from our laptop. ***earthaccess*** handles authentication with [NASA's Earthdata Login (EDL)](https://urs.earthdata.nasa.gov), search using NASA's [CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html) and access through [`fsspec`](https://github.com/fsspec/filesystem_spec).

The only requirement to use this library is to open a free account with NASA [EDL](https://urs.earthdata.nasa.gov).

<a href="https://urs.earthdata.nasa.gov"><img src="https://auth.ops.maap-project.org/cas/images/urs-logo.png" /></a>


### **Authentication**

By default, `earthaccess` with automatically look for your EDL account credentials in two locations:

1. A `~/.netrc` file
2. `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables

If neither of these options are configured, you can authenticate by calling the `earthaccess.login()` method
and manually entering your EDL account credentials.

```python
import earthaccess

earthaccess.login()
```

Note you can pass `persist=True` to `earthaccess.login()` to have the EDL account credentials you enter
automatically saved to a `~/.netrc` file for future use.


Once you are authenticated with NASA EDL you can:

* Get a file from a DAAC using a `fsspec` session.
* Request temporary S3 credentials from a particular DAAC (needed to download or stream data from an S3 bucket in the cloud).
* Use the library to download or stream data directly from S3.
* Regenerate CMR tokens (used for restricted datasets)


### **Searching for data**

Once we have selected our dataset we can search for the data granules using *doi*, *short_name* or *concept_id*.
If we are not sure or we don't know how to search for a particular dataset, we can start with the ["Introducing NASA earthaccess"](https://nsidc.github.io/earthaccess/tutorials/demo/#querying-for-datasets) tutorial or through the [NASA Earthdata Search portal](https://search.earthdata.nasa.gov/). For a complete list of search parameters we can use visit the extended [API documentation](https://nsidc.github.io/earthaccess/user-reference/api/api/).

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

### **Accessing the data**

**Option 1: Using the data links**

If we already have a workflow in place for downloading our data, we can use *earthaccess* as a search-only library and get HTTP links from our query results. This could be the case if our current workflow uses a different language and we only need the links as input.

```python

# if the data set is cloud hosted there will be S3 links available. The access parameter accepts "direct" or "external", direct access is only possible if you are in the us-west-2 region in the cloud.
data_links = [granule.data_links(access="direct") for granule in results]

# or if the data is an on-prem dataset
data_links = [granule.data_links(access="external") for granule in results]

```

> Note: *earthaccess* can get S3 credentials for us, or auhenticated HTTP sessions in case we want to use them with a different library.

**Option 2: Download data to a local folder**

This option is practical if you have the necessary space available on disk. The *earthaccess* library will print out the approximate size of the download and its progress.
```python
files = earthaccess.download(results, "./local_folder")

```

**Option 3: Direct S3 Access - Stream data directly to xarray**

This method works best if you are in the same Amazon Web Services (AWS) region as the data (us-west-2) and you are working with gridded datasets (processing level 3 and above).

```python
import xarray as xr

files = earthaccess.open(results)

ds = xr.open_mfdataset(files)

```

And that's it! Just one line of code, and this same piece of code will also work for data that are not hosted in the cloud, i.e. located at NASA storage centers.


> More examples coming soon!


### Compatibility

Only **Python 3.8+** is supported.




## Contributors

[![Contributors](https://contrib.rocks/image?repo=nsidc/earthaccess)](https://github.com/nsidc/earthaccess/graphs/contributors)

## Contributing Guide

Welcome! 😊👋

> Please see the [Contributing Guide](CONTRIBUTING.md).

### [Project Board](https://github.com/nsidc/earthdata/discussions).

### Glossary

<a href="https://www.earthdata.nasa.gov/learn/glossary">NASA Earth Science Glossary</a>

## License

earthaccess is licensed under the MIT license. See [LICENSE](LICENSE.txt).

## Level of Support

<div><img src="https://raw.githubusercontent.com/nsidc/earthdata/main/docs/nsidc-logo.png" width="84px" align="left" text-align="middle"/>
<br>
 This repository is not actively supported by NSIDC but we welcome issue submissions and pull requests in order to foster community contribution.
</div>

