# Authentication

You can use `earthaccess` to search for datasets and data without needing to log in.
However, to access (download or stream) NASA Earth science data, whether from one of the NASA
Distributed Active Archive Centers (DAACs) on-premises archive or from NASA Earthdata Cloud, you need
an Earthdata Login account.  You can [register for a free Earthdata Login (EDL) account](https://urs.earthdata.nasa.gov/).

Once you have an Earthdata Login account, you may use the `earthaccess.login` method to manage Earthdata Login credentials and, when you are working with cloud-hosted data, cloud credentials.

`earthaccess.login` offers three methods of logging in (or authenticating) using EDL:

* [an interactive login method](#login-interactively), where you enter EDL username and password manually
* an automatic login method using EDL credentials stored in a [`.netrc`](#login-using-a-netrc) file
* an automatic login method using EDL credentials stored in [environment variables](#login-using-environment-variables).

By default, `earthaccess.login()` will look for a `.netrc` or environment variables first.  If neither of these are found, it will prompt you to enter your username and password.  The three methods are described in detail below.

`earthaccess.login` can also be used to login to [different endpoints](#accessing-different-endpoints) and [get S3 credentials](#using-earthaccess-to-get-credentials).

## Login Interactively

If you have not created a `.netrc` file or `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables, you can use the following approach to login.

```python
>>> import earthaccess

>>> auth = earthaccess.login()
Enter your Earthdata Login username: your_username
Enter your Earthdata password:
```

You don't need to assign the result of `earthaccess.login()` to a variable but doing so enables access to session information.  These are discussed in [Accessing Session Information]().

Setting `earthaccess.login(strategy="interactive")` will force a manual login.

## Login using a `.netrc`

!!! warning "Do not use this strategy on untrusted machines or with shared accounts"

    `earthaccess` does not currently support encrypted `.netrc` files.   This strategy of writing credentials in plain text to disk
    should not be used on untrusted machines or shared user accounts.

### Creating a `.netrc` file

#### Using `earthaccess.login` to create a `.netrc` file

You can use `earthaccess.login` to create a `.netrc` for you.

```
earthaccess.login(persist=True)
```

You will then be prompted for your Earthdata Login username and password.  A `.netrc` (or `_netrc`) file will be created automatically.

#### Manually creating a `.netrc` file for Earthdata Login Credentials

=== "MacOS"
    Type the following on your command line, replacing `<username>` and `<password>` with your
    Earthdata Login credentials.

    ```
    echo "machine urs.earthdata.nasa.gov login <username> password <password>" >> $HOME/.netrc
    chmod 600 $HOME/.netrc
    ```

=== "Linux"
    Type the following on your command line, replacing `<username>` and `<password>` with your
    Earthdata Login credentials.

    ```
    echo "machine urs.earthdata.nasa.gov login <username> password <password>" >> $HOME/.netrc
    chmod 600 $HOME/.netrc
    ```

=== "Windows"
    In a `CMD` session, create a `%HOME%` environment variable.  The following line
    creates `%HOME%` from the path in `%USERPROFILE%`, which looks something like
    `C:\Users\"username"`.

    ```
    setx HOME %USERPROFILE%
    ```

    You now need to create a `_netrc` file in `%HOME%`.

    ```
    echo "machine urs.earthdata.nasa.gov login <username> password <password>" >> %HOME%\_netrc
    ```

## Login using environment variables

Alternatively, Earthdata Login credentials can be created as environment variables `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`.

=== "MacOS"
    If you want to set the environment variables for the current shell session, type the following on the command line.

    ```
    export EARTHDATA_USERNAME="username"
    export EARTHDATA_PASSWORD="password"
    ```

    If you want to set these environmental variables permanently, add these two lines to the appropriate configuration files for your operating system.

=== "Linux"
    If you want to set the environment variables for the current shell session, type the following on the command line.

    ```
    export EARTHDATA_USERNAME="username"
    export EARTHDATA_PASSWORD="password"
    ```

    If you use `bash` and would like to set these environmental variables permanently, add these two lines to your `~/.profile` file:

    ```
    EARTHDATA_USERNAME="username"
    EARTHDATA_PASSWORD="password"
    ```

    For other shells, use the recommended method to persistently set these environment variables for whichever shell you use.

=== "Windows"
    To set the environment variables for the current `CMD` session, type the following:

    ```
    setx EARTHDATA_USERNAME "username"
    setx EARTHDATA_PASSWORD "password"
    ```

    To set these environmental variables permanently:

    1. Open the start menu.
    2. Search for the "Advanced System Settings" control panel and click on it.
    3. Click on the "Environment Variables" button toward the bottom of the screen.
    4. Follow the prompts to add the variable to the user table.

## Accessing different endpoints

### Earthdata User Acceptance Testing (UAT) endpoint

If your EDL account is authorized to access the User Acceptance Testing (UAT) environment,
you can set earthaccess to work with its EDL and CMR endpoints
by setting the `system` argument at login, as follows:

```python
import earthaccess

earthaccess.login(system=earthaccess.UAT)
```

## Using `earthaccess` to get S3 credentials

`earthaccess.login` is a very convenient way to manage and provide Earthdata Login credentials.  `earthaccess.login` can also be used to obtain S3 credentials to access NASA Earthdata Cloud.  If you use `earthaccess` to access data in the cloud, you do not have to use this option, `earthaccess` handles this.  However, if you are using other packages, such as `h5coro`, `earthaccess` can save a lot of time.

```python
import earthaccess
import xarray as xr
import h5coro

auth = earthaccess.login()
s3_credentials = auth.get_s3_credentials(daac="NSIDC")

s3url_atl23 = 'nsidc-cumulus-prod-protected/ATLAS/ATL23/001/2023/03/' \
                '01/ATL23_20230401000000_10761801_001_01.h5'
ds = xr.open_dataset(s3url_atl23, engine='h5coro',
                     group='/mid_latitude/beam_1',
                     credentials=s3_credentials)
```
