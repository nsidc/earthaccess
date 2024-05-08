## Authenticate with Earthdata Login

The first step to use NASA Earthdata is to create an account with Earthdata Login, please follow the instructions at [NASA EDL](https://urs.earthdata.nasa.gov/)

Once registered, earthaccess can use environment variables, a `.netrc` file or interactive input from a user to login with NASA EDL.

If a strategy is not especified, env vars will be used first, then netrc and finally user's input.

```py
import earthaccess

auth = earthaccess.login()
```

If you have a .netrc file with your Earthdata Login credentials

```py
auth = earthaccess.login(strategy="netrc")
```

If your Earthdata Login credentials are set as environment variables: EARTHDATA_USERNAME, EARTHDATA_PASSWORD

```py
auth = earthaccess.login(strategy="environment")
```

If you wish to enter your Earthdata Login credentials when prompted with optional persistence to .netrc

```py
auth = earthaccess.login(strategy="interactive", persist=True)
```



### **Authentication**

By default, `earthaccess` with automatically look for your EDL account credentials in two locations:

1. A `~/.netrc` file
2. `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables

If neither of these options are configured, you can authenticate by calling the `earthaccess.login()` method
and manually entering your EDL account credentials.

```python
import earthaccess

earthaccess.login()
```

Note you can pass `persist=True` to `earthaccess.login()` to have the EDL account credentials you enter
automatically saved to a `~/.netrc` file for future use.


Once you are authenticated with NASA EDL you can:

* Get a file from a DAAC using a `fsspec` session.
* Request temporary S3 credentials from a particular DAAC (needed to download or stream data from an S3 bucket in the cloud).
* Use the library to download or stream data directly from S3.
* Regenerate CMR tokens (used for restricted datasets).


