# Authenticate with Earthdata Login using environment variables

!!! important

   You will need a NASA Earthdata Login account to download or stream NASA Earthdata.
   To obtain a NASA Earthdata Login account , please follow the instructions at
   [NASA EDL](https://urs.earthdata.nasa.gov/)


You will need to create two environment variables: `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`.  Instructions for creating these environment variables can be found [here](https://earthaccess.readthedocs.io/en/stable/user/explanation/authenticate/#login-using-environment-variables).

Once you have created your environment variables you can use [`earthaccess.login`](https://earthaccess.readthedocs.io/en/stable/api/#earthaccess.api.login) to authenticate.

```py
import earthaccess

auth = earthaccess.login()
```

You can also set your login strategy explicitly by setting `strategy="environment"`.

```py
auth = earthaccess.login(strategy="environment")
```

!!! note

   Alternatively, you can use an existing Earthdata Login token by setting the environment
   variable `EARTHDATA_TOKEN` to it and using the same "environment" strategy, above.

See the [Authetication](https://earthaccess.readthedocs.io/en/stable/user/explanation/authenticate/#login-using-environment-variables) explanation page for more details.