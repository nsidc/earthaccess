# _earthaccess_

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


`earthaccess` is a python library to **search for**, and **download** or **stream** NASA Earth science data with just a few lines of code.

Visit [our documentation](https://earthaccess.readthedocs.io/en/latest) to learn more!

Try it in your browser without installing anything! [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nsidc/earthaccess/main)

## Why `earthaccess`

During several workshops organized by NASA Openscapes, the need to provide easy-to-use tools to our users became evident. Open science is a collaborative effort; it involves people from different technical backgrounds, and the data analysis to solve the pressing problems we face cannot be limited by the complexity of the underlying systems. Therefore, providing easy access to NASA Earthdata regardless of the data storage location (hosted within or outside of the cloud) is the main motivation behind this Python library.


## How to Get Started with `earthaccess`

### How to install

To install `earthaccess` go to your terminal and install it using `pip`:

```
python -m pip install earthaccess
```


### How to access NASA Earth Science data

With _earthaccess_, data is 3 steps away!

```python
import earthaccess

# 1. Login
earthaccess.login()

# 2. Search
results = earthaccess.search_data(
    short_name='ATL06',  # ATLAS/ICESat-2 L3A Land Ice Height
    bounding_box=(-10, 20, 10, 50),  # Only include files in area of interest...
    temporal=("1999-02", "2019-03"),  # ...and time period of interest.
    count=10
)

# 3. Access
files = earthaccess.download(results, "/tmp/my-download-folder")
```

Visit [our quick start guide](https://earthaccess.readthedocs.io/en/latest/quick-start/) for more details.


## Help!

We're here for you!
**Before you open a new issue/discussion/topic, please search to see if anyone else has
opened a similar one.**

:bug: If you've found a bug or mistake, please use
[GitHub issues](https://github.com/nsidc/earthaccess/issues).

:bulb: If you'd like to request a feature or ask a question, please use
[GitHub discussions](https://github.com/nsidc/earthaccess/discussions).

:left_speech_bubble: If you prefer real-time chat, please visit us in our
[Zulip chat space](https://earthaccess.zulipchat.com)!
We'd love to see you there! :open_hands:


## Compatibility

The _minimum_ supported Python version is **3.11**.


## How to Contribute to `earthaccess`

If you want to contribute to `earthaccess` checkout the [Contributing Guide](https://earthaccess.readthedocs.io/en/latest/contributing/).


### Contributors

[![Contributors](https://contrib.rocks/image?repo=nsidc/earthaccess)](https://github.com/nsidc/earthaccess/graphs/contributors)


### [Project Board](https://github.com/nsidc/earthdata/discussions).
