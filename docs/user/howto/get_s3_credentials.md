# How do I get AWS S3 credentials?

## Problem

I would like to retrieve credentials to access data in an S3 bucket.

## Solution

S3 credentials are bucket specific.  Buckets are organized by DAAC[^1]

```
import earthaccess

auth = earthaccess.login()
s3_credentials = auth.get_s3_credentials(daac="NSIDC")
```

The DAAC responsible for a Data Collection can be found from the `provider_id` in the result returned by `search_datasets`.

[^1]: Distributed Active Archive Center.  