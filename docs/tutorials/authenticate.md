## Authenticate with Earthdata Login

Import the Auth class 
```py
from earthaccess import Auth
```

If you have a .netrc file with your Earthdata Login credentials

```py
auth = Auth().login(strategy="netrc")
```

If your Earthdata Login credentials are set as environment variables: EDL_USERNAME, EDL_PASSWORD

```py
auth = Auth().login(strategy="environment")
```

If you wish to enter your Earthdata Login credentials when prompted 

```py
auth = Auth().login(strategy="interactive")
```
