# _earthaccess_

<p align="center">
<img alt="earthaccess, a python library to search, download or stream NASA Earth science data with just a few lines of code" src="https://user-images.githubusercontent.com/717735/205517116-7a5d0f41-7acc-441e-94ba-2e541bfb7fc8.png" width="70%" align="center" />
</p>

<p align="center">

<a href="https://doi.org/10.5281/zenodo.8365009" target="_blank">
    <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.8365009.svg" alt="DOI" />
</a>

<a href="https://x.com/allison_horst" target="_blank">
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

<a href="https://github.com/earthaccess-dev/earthaccess/actions/workflows/test.yml" target="_blank">
    <img src="https://github.com/earthaccess-dev/earthaccess/actions/workflows/test.yml/badge.svg" alt="Unit Tests status" />
</a>

<a href="https://github.com/pyOpenSci/software-review/issues/302" target="_blank">
    <img src="https://pyopensci.org/badges/peer-reviewed.svg" alt="pyOpenSci Peer-Reviewed" />
</a>

</p>

`earthaccess` is a python library to **search for**, and **download** or **stream** NASA Earth science data with just a few lines of code.

Visit [our documentation](https://earthaccess.readthedocs.io/en/latest) to learn more!

## Why `earthaccess`

During several workshops organized by NASA Openscapes, the need to provide easy-to-use tools to our users became evident. Open science is a collaborative effort; it involves people from different technical backgrounds, and the data analysis to solve the pressing problems we face cannot be limited by the complexity of the underlying systems. Therefore, providing easy access to NASA Earthdata regardless of the data storage location (hosted within or outside of the cloud) is the main motivation behind this Python library.


## How to Get Started with `earthaccess`

### How to install

To install `earthaccess` go to your terminal and install it using `pip`:

```
python -m pip install earthaccess
```


### How to access NASA Earth Science data

**You'll need a free NASA Earthdata Login (EDL) account.** If you don't have one yet,
[register here](https://urs.earthdata.nasa.gov/). `earthaccess.login()`
prompts you for these credentials (or reads them from a `.netrc` file or environment
variables). See
[Authenticate with Earthdata Login](https://earthaccess.readthedocs.io/en/latest/user/howto/authenticate/)
for details.

With _earthaccess_, data is 3 steps away!

```python
import earthaccess

# 1. Login
earthaccess.login()

# 2. Search
results = earthaccess.search_data(
    short_name="ATL06",  # ATLAS/ICESat-2 L3A Land Ice Height
    bounding_box=(-10, 20, 10, 50),  # Only include files in area of interest...
    temporal=("1999-02", "2019-03"),  # ...and time period of interest.
    count=10,
)

# 3. Access
files = earthaccess.download(results, "/tmp/my-download-folder")
```

Visit [our quick start guide](https://earthaccess.readthedocs.io/en/latest/user/quick-start/) for more details.


## Help!

We're here for you!
**Before you open a new issue/discussion/topic, please search to see if anyone else has
opened a similar one.**

:bug: If you've found a bug or mistake, please use
[GitHub issues](https://github.com/earthaccess-dev/earthaccess/issues).

:bulb: If you'd like to request a feature or ask a question, please use
[GitHub discussions](https://github.com/earthaccess-dev/earthaccess/discussions).

:left_speech_bubble: If you prefer real-time chat, please visit us in our
[Zulip chat space](https://earthaccess.zulipchat.com)!
We'd love to see you there! :open_hands:


## Compatibility

The _minimum_ supported Python version is **3.12**.


## How `earthaccess` relates to other tools

`earthaccess` ties search, authentication, and data access together into a single workflow, building on existing open-source tools rather than replacing
them. Other tools in the NASA Earth science data ecosystem include:

- **[VirtualiZarr](https://github.com/zarr-developers/VirtualiZarr)** — builds a virtual Zarr store interface over archival files (netCDF/HDF5) without duplicating data. `earthaccess` integrates it directly via `earthaccess.virtualize()`, turning a set of granules into a virtual xarray `Dataset`, which supports cloud-native access patterns without downloads required.

- **[python-cmr](https://github.com/nasa/python_cmr)** — wraps NASA's Common Metadata
  Repository (CMR) search API. `earthaccess` builds on it, adding provider-aware
  resolution, cloud-hosting filters, and rich result objects.
- **[asf_search](https://github.com/asfadmin/Discovery-asf_search)** — search and access
  tailored to synthetic aperture radar (SAR) data, whereas `earthaccess` is mission- and
  domain-agnostic.
- **[icepyx](https://github.com/icesat2py/icepyx)** — ICESat-2-specific search and access
  that uses `earthaccess` for authentication.
- **[earthdatalogin](https://github.com/boettiger-lab/earthdatalogin)** — analogous
  authentication and access tool for the R ecosystem.
- **[fsspec](https://github.com/fsspec/filesystem_spec) / [s3fs](https://github.com/fsspec/s3fs)**
  — general-purpose filesystem libraries that advanced users can compose manually;
  `earthaccess` encapsulates the NASA-specific authentication and cloud-detection logic
  on top of them.


## Citing `earthaccess`

If you use `earthaccess` in your work, please cite it. The version-specific
citation can be generated from the "Cite this repository" button on the
[GitHub repository](https://github.com/earthaccess-dev/earthaccess) (powered by
`CITATION.cff`). For convenience, a general citation using the Zenodo DOI is:

> Barrett, A., Battisto, C., Bourbeau, J., Carroll, I., Daniels, C., Fisher, M.,
> Kaufman, D., Kennedy, J.H., Lopez, L., Lowndes, J., Scheick, J., Steiker, A., &
> Varghese, S. _earthaccess_ [Computer software]. Zenodo.
> https://doi.org/10.5281/zenodo.8365009

```bibtex
@software{earthaccess,
  author    = {Barrett, Andrew and Battisto, Chris and Bourbeau, James and Carroll, Ian and Daniels, Chuck and Fisher, Matt and Kaufman, Daniel and Kennedy, Joseph H. and Lopez, Luis and Lowndes, Julia and Scheick, Jessica and Steiker, Amy and Varghese, Sherwin},
  title     = {earthaccess},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.8365009},
  url       = {https://doi.org/10.5281/zenodo.8365009}
}
```

<!-- TODO: replace with the JOSS paper citation once the JOSS submission is published. -->


## How to Contribute to `earthaccess`

If you want to contribute to `earthaccess` checkout the [Contributing Guide](https://earthaccess.readthedocs.io/en/latest/contributor/).


### Contributors

[![Contributors](https://contrib.rocks/image?repo=earthaccess-dev/earthaccess)](https://github.com/earthaccess-dev/earthaccess/graphs/contributors)
