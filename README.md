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
pip install earthdata
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
from earthdata import Auth, DataGranules, DataCollections, Accessor

auth = Auth() # if we want to access NASA DATA in the cloud
auth.login()

collections = DataCollections(auth).keyword('MODIS').get(10)

granules = DataGranules(auth).concept_id('C1711961296-LPCLOUD').bounding_box(-10,20,10,50).get(5)

# We provide some convenience functions for each result
data_links = [granule.data_links() for granule in granules]

# The Acessor class allows to get the granules from on-prem locations with get()
# NOTE: Some datasets require users to accept a Licence Agreement before accessing them
access = Accessor(auth)

# This works with both, on-prem or cloud based collections**
access.get(granules, './data')

# if you're in a AWS instance (us-west-2) you can use open() to get a fileset!
fileset = accessor.open(granules)

xarray.open_mfdataset(fileset, combine='by_coords')
```

Only **Python 3.7+** is supported as required by the black, pydantic packages


## Contributing Guide

Welcome! 😊👋

> Please see the [Contributing Guide](CONTRIBUTING.md).
