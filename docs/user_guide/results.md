# Results

## Overview


## Exploring results from `search_datasets`


## Exploring results from `search_data`


Services
This is a really big object
```
In [24]: result[0].services()
```

S3 bucket
Currently empty or is it because not cloud-hosted
```
result[0].s3_bucket()
```

cloud_hosted
```
result[0].cloud_hosted
```

landing page is empty for example
```
In [24]: result[0].landing_page()
```

Data type
```
In [24]: result[0].data_type()
Out[24]: "[{'FormatType': 'Native', 'Format': 'HDF5', 'FormatDescription': 'HTTPS'}]"
```

Abstract
```
result[0].abstract()
```
