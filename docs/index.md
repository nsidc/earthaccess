---
hide:
  - toc
---


# earthaccess 🌍

<p align="center">
    <em>Python library to search, download or stream NASA Earth science data</em>
</p>

<p align="center">
<a href="https://github.com/betolink/earthdata/actions?query=workflow%3ATest" target="_blank">
    <img src="https://github.com/betolink/earthdata/workflows/Test/badge.svg" alt="Test">
</a>
<a href="https://github.com/betolink/earthdata/actions?query=workflow%3APublish" target="_blank">
    <img src="https://github.com/betolink/earthdata/workflows/Publish/badge.svg" alt="Publish">
</a>
<a href="https://pypi.org/project/earthdata" target="_blank">
    <img src="https://img.shields.io/pypi/v/earthdata?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://pypi.org/project/earthdata/" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/earthdata.svg" alt="Python Versions">
</a>
<a href="https://github.com/psf/black" target="_blank">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
</a>

</p>

---

## Overview

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/betolink/earthdata/main)

A Python library to search, download or stream NASA Earth Science data with just a few lines of code.

## Installing earthdata

Install the latest release:

```bash
conda install -c conda-forge earthaccess
```

## Example Usage

# Authentication
Authenticate using your Earthdata Login (EDL) credentials. If you have a .netrc file with these credentials in it will read that, otherwise it will prompt for your EDL username and password. 
```py
import earthaccess

auth = earthaccess.login(strategy="netrc")
if not auth:
    auth = earthacess.login(strategy="interactive", persist=True)
```

# Searching for data 
Search for granules (files) within a data set (e.g. ATL06)

```py
results = earthaccess.search_data(
    short_name='ATL06',
    version="005",
    cloud_hosted=True,
    bounding_box=(-10, 20, 10, 50),
    temporal=("2020-02", "2020-03"),
    count=100
)    
```

# Accessing the data

Option 1: Obtaining the data links 

```py
# if the data are on-prem you can obtain the HTTPS links 
data_links = [granule.data_links(access="external") for granule in results]

# if the data are in the cloud, S3 links are available
data_links = [granule.data_links(access="direct") for granule in results]
```
Option 2: Download data to a local folder 

```py
files = earthaccess.download(results, "./local_folder")
```

Option 3: Direct S3 Access - Stream the data directly to xrray 

```py 
ds = xr.open_mfdataset(earthaccess.open(results, auth=auth), engine="scipy")
```

For more examples see the `Demo` and `EarthdataSearch` notebooks.


Only **Python 3.7+** is supported as required by the black, pydantic packages


## Code of Conduct

See [Code of Conduct](https://github.com/nsidc/earthdata/blob/main/CODE_OF_CONDUCT.md)

## Level of Support

* This repository is not actively supported by NSIDC but we welcome issue submissions and pull requests in order to foster community contribution.

<img src="nsidc-logo.png" width="84px" />

## Contributing Guide

Welcome! 😊👋

You can clone `earthaccess` and get started locally

```bash

# ensure you have Poetry installed
pip install --user poetry

# install all dependencies (including dev)
poetry install

# develop!
```

> Please see the [Contributing Guide](https://github.com/nsidc/earthdata/blob/main/CONTRIBUTING.md)
