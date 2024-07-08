### **Accessing the data**

**Option 1: Using the data links**

If we already have a workflow in place for downloading our data, we can use *earthaccess* as a search-only library and get HTTP links from our query results. This could be the case if our current workflow uses a different language and we only need the links as input.

```python

# if the data set is cloud-hosted there will be S3 links available. The access parameter accepts "direct" or "external". Direct access is only possible if you are in the us-west-2 region in the cloud.
data_links = [granule.data_links(access="direct") for granule in results]

# or if the data is an on-prem dataset
data_links = [granule.data_links(access="external") for granule in results]

```

> Note: *earthaccess* can get S3 credentials for us, or authenticated HTTP sessions in case we want to use them with a different library.

**Option 2: Download data to a local folder**

This option is practical if you have the necessary space available on disk. The *earthaccess* library will print out the approximate size of the download and its progress.
```python
files = earthaccess.download(results, "./local_folder")

```

**Option 3: Direct S3 Access - Stream data directly to xarray**

This method works best if you are in the same Amazon Web Services (AWS) region as the data (us-west-2) and you are working with gridded (processing level 3 and above) datasets without nested or hierarchical data variables.

```python
import xarray as xr

files = earthaccess.open(results)

ds = xr.open_mfdataset(files)

```

And that's it in just one line of code! This same piece of code will also work for data that are not hosted in the cloud, i.e. located at NASA storage centers.


> More examples coming soon!
