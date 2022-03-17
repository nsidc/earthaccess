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



## Overview

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/betolink/earthdata/main)

A Python library to search and access NASA datasets.

## Installing earthdata

Install the latest release:

```bash
conda install -c conda-forge earthdata
```

Or you can clone `earthdata` and get started locally

```bash

# ensure you have Poetry installed
pip install --user poetry

# install all dependencies (including dev)
poetry install

# develop!
```

## Example Usage

```python
from earthdata import Auth, DataGranules, DataCollections, Store

auth = Auth().login() # if we want to access NASA DATA in the cloud

# To search for collecrtions (datasets)

DatasetQuery = DataCollections().keyword('MODIS').bounding_box(-26.85,62.65,-11.86,67.08)

counts = DatasetQuery.hits()
collections = DatasetQuery.get()


# To search for granules (data files)
GranuleQuery = DataGranules().concept_id('C1711961296-LPCLOUD').bounding_box(-10,20,10,50)

# number of granules (data files) that matched our criteria
counts = GranuleQuery.hits()
# We get the metadata
granules = GranuleQuery.get(10)

# earthdata provides some convenience functions for each data granule
data_links = [granule.data_links() for granule in granules]

# The Store class allows to get the granules from on-prem locations with get()
# NOTE: Some datasets require users to accept a Licence Agreement before accessing them
store = Store(auth)

# This works with both, on-prem or cloud based collections**
store.get(granules, local_path='./data')

# if you're in a AWS instance (us-west-2) you can use open() to get a fileset!
fileset = store.open(granules)

# Given that this is gridded data we could
xarray.open_mfdataset(fileset, combine='by_coords')
```

For more examples see the `Demo` and `EarthdataSearch` notebooks.


Only **Python 3.7+** is supported as required by the black, pydantic packages


## Code of Conduct

See [Code of Conduct](CODE_OF_CONDUCT.md)

## Level of Support

* This repository is not actively supported by NSIDC but we welcome issue submissions and pull requests in order to foster community contribution.

<img src="docs/nsidc-logo.png" width="84px" />

## Contributing Guide

Welcome! 😊👋

> Please see the [Contributing Guide](CONTRIBUTING.md).
