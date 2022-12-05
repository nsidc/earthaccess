---
hide:
  - toc
---


# earthdata 🌍

<p align="center">
    <em>Client library for NASA CMR and EDL APIs</em>
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

A Python library to search and access NASA datasets.

## Installing earthdata

Install the latest release:

```bash
conda install -c conda-forge earthaccess
```

## Example Usage

```py
from earthdata import Auth, DataGranules, DataCollections, Store

# Authenticate using your Earthdata login credentials (do these need to be saved in a .netrc file?)
auth = Auth().login() # if we want to access NASA DATA in the cloud

# Search for granules (files) within a data set
GranuleQuery = DataGranules().concept_id('C1711961296-LPCLOUD').bounding_box(-10,20,10,50)

# Count the number of granules that match this search criteria
counts = GranuleQuery.hits()

# Retrieve the metadata for the first 10 granules
granules = GranuleQuery.get(10)

# Find the download links for each granule within the metadata
data_links = [granule.data_links() for granule in granules]

# Download on-prem granules 
store = store(Auth)
store.get(granules, local_path='./data')

# Or if you are in an AWS instance (region us-west-2) you can use open to stream a file
fileset = store.open(granules)


# You can also search and retrieve metdata for collections (data sets)

DatasetQuery = DataCollections().keyword('MODIS').bounding_box(-26.85,62.65,-11.86,67.08)

counts = DatasetQuery.hits()
collections = DatasetQuery.get()
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
