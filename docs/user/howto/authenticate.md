# Authenticate with Earthdata Login

!!! important
    
    You will need a NASA Earthdata Login account to download or stream NASA Earthdata.
    To obtain a NASA Earthdata Login account , please follow the instructions at
    [NASA EDL](https://urs.earthdata.nasa.gov/)


Once you have a NASA Earthdata Login account you can use [`earthaccess.login`](https://earthaccess.readthedocs.io/en/stable/api/#earthaccess.api.login) to authenticate.

```py
import earthaccess

auth = earthaccess.login()
```

By default `earthaccess.login` will try several strategies to get your login credentials.  First, it will look to see if your
Earthdata Login credentials are set as environment variables `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`.  Next, it will
look to see if you have a `.netrc` file with your Earthdata Login credentials.  If none of these strategies are available, you will be
prompted to enter your username and password.

See the [Authetication](https://earthaccess.readthedocs.io/en/stable/user/explanation/authenticate/#login-using-environment-variables) explanation page for more details.