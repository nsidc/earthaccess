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

## **Welcome to `earthaccess`**

`earthaccess` is a python library to **search for**, and **download** or **stream** NASA Earth science data with just a few lines of code.

Open science only reaches its full potential if we have easy-to-use workflows that facilitate research in an inclusive, efficient and reproducible way. Unfortunately —as it stands today— scientists and students alike face a steep learning curve adapting to systems that have grown too complex and end up spending more time on the technicalities of the tools, cloud and NASA APIs than focusing on their important science.

During several workshops organized by [NASA Openscapes](https://nasa-openscapes.github.io/events.html), the need to provide easy-to-use tools to our users became evident. Open science is a collaborative effort; it involves people from different technical backgrounds, and the data analysis to solve the pressing problems we face cannot be limited by the complexity of the underlying systems. Therefore, providing easy access to NASA Earthdata regardless of the data storage location (hosted within or outside of the cloud) is the main motivation behind this Python library.

***earthaccess*** handles authentication with [NASA's Earthdata Login (EDL)](https://urs.earthdata.nasa.gov), search using NASA's [CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html) and access through [`fsspec`](https://github.com/fsspec/filesystem_spec).

Try it in your browser without installing anything! [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nsidc/earthaccess/main)


## **Getting Started**

### **Installing earthaccess**

The latest release of `earthaccess` can be installed with `mamba`, `conda` or `pip`.  We recommend using `mamba` because it is faster.

You will need Python 3.8 or higher installed.

#### Using `mamba`

```bash
mamba install -c conda-forge earthaccess
```

#### Using `conda`

```bash
conda install -c conda-forge earthaccess
```

#### Using `pip`

```bash
pip install earthaccess
```


### Check `earthaccess` is installed

This should run seamlessly (fingers-crossed).  To check `earthaccess` is correctly installed you can start a python interpreter (either python or ipython) and run the following code.

```
$ python
Python 3.12.1 | packaged by conda-forge | (main, Dec 23 2023, 08:03:24) [GCC 12.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import earthaccess
>>> earthaccess.__version__
'0.8.2'
```

> Note:
> Your `python` and `earthaccess` versions may be different.


## **Get Data in 3 Steps**

`earthaccess` allows you to search for and access data in as little as three steps.  We give a very quick example below.  These three steps allow you to get data whether you are working in the cloud or on your local laptop or workstation.  Read the [User Guide](user_guide.qmd) for more information.  If you want to quickly find how to perform some common searches and data access,
take a look at our [How-to](how_to.qmd) guide.

The only requirement to use this library is to open a free account with NASA [EDL](https://urs.earthdata.nasa.gov).

### Step 1: Login

To access NASA data, you have to login using your Earth Data Login credentials.  You can register for a free Earth Data Login account [here](https://urs.earthdata.nasa.gov/).

By default, `earthaccess` will look for your Earth Data Login credentials in a `.netrc` file, or in environment variables `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`.  If you don't
have either of these set up, you can login manually.  See [Authenticating](authenticate.qmd) to learn how to create a `.netrc` file or environment variables.

```
import earthaccess

earthaccess.login()
```


### Step 2: Search for data

As an example, we'll search for data from the NASA ICESat-2 mission.  ATL06


```
results = earthaccess.search_data(
    short_name='ATL06'
    bounding_box=(-10, 20, 10, 50),
    temporal=("1999-02", "2019-03"),
    count=10
)
```

### Step 3. Download the files

Once you have found the files you want, you can download them to your local machine.

```
files = earthaccess.download(results, "./local_folder")
```

If you are working in the cloud and the data files are hosted in the cloud, you can stream the data directly, without having to download data.  See [Direct S3 Access]()


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
 This repository is supported by a joint effort of NSIDC, NASA DAACs, and the Earth science community, and we welcome any contribution in the form of issue submissions, pull requests, or discussions. Issues labeled as https://github.com/nsidc/earthaccess/labels/good%20first%20issue are a great place to get started.
</div>

