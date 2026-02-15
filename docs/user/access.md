# Access

## Overview

The are two **access** methods available in `earthaccess`.  The first method is `download`, which downloads a file or files to a local computer, a laptop, workstation or the storage space for a high-performace-computer (HPC).  The second method is `open`, which streams data directly into memory.  Streaming data is analogous to streaming a TV show or film.  This approach can be used whethor you are accessing data from a local machine or accessing data from a cloud-hosted Jupyter Hub or other cloud computing environment but is most useful when you are working in the cloud.

!!!note "You must login to download or stream data"

    You need to authenticate using `earthaccess.login` to download or stream data.  See the [Access](./access.md) section of the User Guide for more information.

## Downloading data

### Basic download

`earthaccess.download` only requires a list of results returned by `search_data`.

```python
filelist = earthaccess.download(results)
```
```
QUEUEING TASKS | : 100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00, 1706.04it/s]
PROCESSING TASKS | : 100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:13<00:00,  6.89s/it]
COLLECTING RESULTS | : 100%|████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00, 26379.27it/s]
```

If you want to download a single elements from results, for example `results[0]`, you have make sure you pass a list to `download`, this is done by putting the single element inside square brackets.

```python
filelist = earthaccess.download([results[0]])
```

By default files are downloaded to a sub-directory of the current working directory with a name similar to `./data/YYYY-MM-DD_UUID`, where `YYYY-MM-DD` is the year, month and day of the current date, and `UUID` is a unique identifier.  The path to each file is returned and, here, stored in the variable `filelist`.

```python
filelist
```

```
[PosixPath('/current/working/directory/data/2025-09-12-c58fe9/ATL10-01_20181014000347_02350101_006_02.h5'),
 PosixPath('/current/working/directory/data/2025-09-12-c58fe9/ATL10-01_20181014000347_02350101_007_01.h5')]
```

You can override this behaviour by setting the `local_path` keyword to a local directory.

```python
filelist = earthaccess.download(results, local_path='/path/to/local/data/directory/')
```

The progress bar is displayed if you are in an interactive session such as a notebook or IPython session.  Otherwise the progress bar is not displayed.  Whether or not the progress bar is displayed is controlled by setting `show_progress=True` or `show_progress=True`.

The list of files in `filelist`, or one element of that list can be passed to an application such as `xarray` to load the data for analysis.

```python
ds = xarray.open_mfdataset(filelist)
```

or

```python
ds = xarray.open_dataset(filelist[0])
```

See `download` documentation in the User Reference section for more information.


## Streaming data

### A basic streaming access pattern

Streaming data is an efficient way to access data, without downloading and saving it to disk.  This is especially useful if you are working in a cloud-hosted computing environment such as a Jupyter Hub or Google CoLab because storing data incurrs charges.  Streaming data when you are working in a cloud computing environment in the same region as the data are stored because connections between the computing and storage environments have high bandwidth.  For NASA Earthdata, this is the AWS region `us-west-2`.

Streaming data with the `open` method is very similar to `download`.

```python
fileobjects = earthaccess.open(results)
```
```
QUEUEING TASKS | : 100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00, 1706.04it/s]
PROCESSING TASKS | : 100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:13<00:00,  6.89s/it]
COLLECTING RESULTS | : 100%|████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00, 26379.27it/s]
```

Rather than returning a list of paths, `earthaccess.open` returns a list of _file-like objects_.  These can be used in the same way as a filepath with third-party applications such as `xarray`.

```python
ds = xarray.open_mfdataset(fileobjects)
```

or

```python
ds = xarray.open_dataset(fileobjects[0])
```


## Optimizing `earthaccess.open`

When using `earthaccess.open` to stream data from NASA Earthdata cloud, access times depend on the file format of the data you want to stream and how this data is read by the tools you are using (e.g. `xarray`, `pandas`, `pyarrow`).  The default access strategies and parameters for `earthaccess.open` have been chosen to give good performance for the broad range of datasets, file formats and structures archived by NASA.  However, for specific datasets, fine tuning access strategy and parameters may provide improved performance.  Fine tuning access is done by setting parameters in `fsspec_open_kwargs`.

Here, we give a brief overview of the default parameters.  For more nformation see this [Gist](https://gist.github.com/betolink/94aef93ad09f80b09132b8a009561049).  Some of this gets technical.  If it is too technical, just go ahead and use the defaults.  Or ask a question in the `earthaccess GitHub [Issues](https://github.com/nsidc/earthaccess/issues).

`earthaccess.open` uses [`fsspec`](https://filesystem-spec.readthedocs.io/en/latest/) to access data stored in NASA Earthdata cloud.  `fsspec` provides a standard interface to local, remote and embedded file systems and byte storage.  Essentially, it allows you (and Python tools) to treat remote file storage as virtual file system in the same way you would interact with your local file system.

Two key parameters control the efficiency of file access; cache type and block-size.  The default cache type in `earthaccess` is `blockcache`.  Block-size is set depending on the file size as follows:

| File Size |  | Block Size |
|---------|--|----------|
| Small | < 1000 MB | 4 MB |
| Medium | < 1 GB | 8 MB |
| Large | > 1 GB | 16 MB |
