# Quick Start

## **Installing earthaccess**

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
python -m pip install earthaccess
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

`earthaccess` allows you to search for and access data in as little as three steps.  We
give a very quick example below.  These three steps allow you to get data whether you
are working in the cloud or on your local laptop or workstation.  Read the
[User Guide](user_guide/index.md) for more information.  If you want to quickly find how
to perform some common searches and data access, take a look at our how-to guides in the
sidebar.

The only requirement to use this library is to open a free account with NASA
[Earthdata Login](https://urs.earthdata.nasa.gov).

The following steps can be executed in a Python interpreter, a Python file, or a
[Jupyter notebook](https://docs.jupyter.org/en/latest/start/index.html).

### Step 1: Login

To access NASA data, you have to login using your Earth Data Login credentials.  You can register for a free Earth Data Login account [here](https://urs.earthdata.nasa.gov/).

By default, `earthaccess` will look for your Earth Data Login credentials in a `.netrc` file, or in environment variables `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`.  If you don't
have either of these set up, you can login manually.  See [Authenticating](howto/authenticate.md) to learn how to create a `.netrc` file or environment variables.

```python
import earthaccess

earthaccess.login()
```


### Step 2: Search for data

As an example, we'll search for the "ATLAS/ICESat-2 L3A Land Ice Height", or ATL06, dataset from the NASA [ICESat-2](https://nsidc.org/data/icesat-2) mission.


```python
results = earthaccess.search_data(
    short_name='ATL06',
    bounding_box=(-10, 20, 10, 50),
    temporal=("1999-02", "2019-03"),
    count=10
)
```

### Step 3. Download the files

Once you have found the files you want, you can download them to your local machine.

```python
files = earthaccess.download(results, "./local_folder")
```

!!! note

    This will download the data to a directory named `local_folder` in your current
    working directory (the directory from which you are running this code, also known as
    `.`).  If that directory doesn't exist, it will be created automatically.

Data can also be opened in-memory with `earthaccess.open()`. See [our API
docs](user-reference/api/api.md) for more.


We value your feedback! We want to hear all about your experience using earthaccess. Even if you're not noticing any issues or bugs, we want to know... what annoys you? What feels great? We'd love if you would share an experience [report](https://github.com/nsidc/earthaccess/issues/new/choose) with us!
