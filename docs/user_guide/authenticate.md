# Authentication

You can use `earthaccess` to search for datasets and data without needing to login.  However, to access (download or stream) NASA Earth science data, whether from one of the NASA
Distributed Active Archive Centers (DAACs) or from the cloud, you need
an Earthdata Login.  You can register for a a free Earthdata Login (EDL) account [here](https://urs.earthdata.nasa.gov/).  

Once you have an Earthdata Login, the `earthaccess.login` method manages Earthdata Login and cloud credentials, when you are working with cloud-hosted data.  `earthaccess.login` offers three methods of logging in (or authenticating) using EDL: a manual login method, where you enter EDL username and password manually; and two automatic login methods using EDL credentials stored in a `.netrc` file or in environment variables `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`.  By default, `earthaccess.login()` will look for a `.netrc` or environment variables first.  If neither of these are found, it will prompt you to enter your username and password.  The three methods are described in detail below.  

!!! note "This Page is a Work in Progress"

    We are reorganizing and updating the documentation, so not all pages are complete.  If you are looking for information about authenticating using earthaccess see the
    How-Tos and Tutorials in links below.

    * [Quick start](../quick-start.md)
    * [How-To Authenticate with earthaccess](../howto/authenticate.md)


## Login Manually

If you have not created a `.netrc` file or `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, you can use the following approach to login.

```
>>> import earthaccess

>>> auth = earthaccess.login()
Enter your Earthdata Login username: your_username
Enter your Earthdata password: 
```

You don't need to assign the result of `earthaccess.login()` to a variable but doing so enables access session information.  These are discussed in [Accessing Session Information]().

Setting `strategy=interactive` will force a manual login.

## Login using a `.netrc`

### Creating a `.netrc` file

#### Manually creating a `.netrc` file

[Need Linux, MacOS and Windows option]

#### Using `earthaccess.login` to create a `.netrc` file

[Need Linux, MacOS and Windows option]

## Login using environment variables

[Need Linux, MacOS and Windows option]


## Accessing different endpoints

### Earthdata User Acceptance Testing (UAT) environment

If your EDL account is authorized to access the User Acceptance Testing (UAT) system,
you can set earthaccess to work with its EDL and CMR endpoints
by setting the `system` argument at login, as follows:

```python
import earthaccess

earthaccess.login(system=earthaccess.UAT)

```
