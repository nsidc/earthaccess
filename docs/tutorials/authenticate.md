## Authenticate with Earthdata Login

Import earthaccess
```py
from earthaccess
```

If you have a .netrc file with your Earthdata Login credentials

```py
auth = earthaccess.login(strategy="netrc")
```

If your Earthdata Login credentials are set as environment variables: EDL_USERNAME, EDL_PASSWORD

```py
auth = earthaccess.login(strategy="environment")
```

If you wish to enter your Earthdata Login credentials when prompted 

```py
auth = earthaccess.login(strategy="interactive", persist=True)
```
