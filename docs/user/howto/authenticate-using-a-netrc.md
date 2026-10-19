# Authenticate with Earthdata Login stored in a `.netrc`

!!! important
    
    You will need a NASA Earthdata Login account to download or stream NASA Earthdata.
    To obtain a NASA Earthdata Login account , please follow the instructions at
    [NASA EDL](https://urs.earthdata.nasa.gov/)


Once you have a NASA Earthdata Login account you will need to create a `.netrc`.
Instructions for creating a `.netrc` are [here](https://earthaccess.readthedocs.io/en/stable/user/explanation/authenticate/#login-using-a-netrc)

Once you have created a `.netrc` you can authenticate using [`earthaccess.login`](https://earthaccess.readthedocs.io/en/stable/api/#earthaccess.api.login):

```py
import earthaccess

auth = earthaccess.login()
```

Or if you want to specify a longin strategy explicitly:

```py
auth = earthaccess.login(strategy="netrc")
```

See the [Authetication](https://earthaccess.readthedocs.io/en/stable/user/explanation/authenticate/#login-using-environment-variables) explanation page for more details.