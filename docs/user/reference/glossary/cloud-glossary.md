# CLOUD COMPUTING TERMINOLOGY

This guide demystifies key cloud computing terms you'll need to know when working with NASA Earthdata, empowering you to harness the full potential of cloud-based Earth science workflows.

## In-region vs Out-of-region

**In-region**: In-region refers to compute resources running in the same cloud computing region as where the data is stored. NASA Earthdata is primarily hosted in the Amazon Web Services (AWS) `us-west-2` region. Accessing data directly in the cloud from the `us-west-2` Simple Storage Solution (S3) region is free to the user.

**Out-of-region**: When your compute resources are running locally, or in a different AWS region than where the data is stored. Data from NASA Earthdata's S3 buckets currently cannot be accessed from a different AWS region. In general, out-of-region access incurs egress charges and typically slower data transfer speeds.

## Cloud Optimized

Cloud-optimized refers to data, workflows, and computing approaches that are specifically designed or adapted to leverage cloud computing capabilities for efficient, scalable Earth science analysis.

Want to learn more? The team at Development Seed created an amazing [zine](https://zines.developmentseed.org/zines/cloud-native/#zine/1/) that transforms complex concepts into digestible, visual stories.

## File-like access to remote data

**`fsspec`**: Python library providing a filesystem-like interface over remote storage (S3, HTTP, etc.), enabling file-like objects for non-local data.

**`s3fs`**: the `fsspec` implementation for S3, used when `earthaccess` resolves direct `s3://` URIs in-region.

**Byte-range request**: an HTTP/S3 request for a specific slice of bytes from an object, rather than the whole thing. It is the mechanism underlying all lazy/streamed reads.

**Block cache**: `fsspec`'s strategy of fetching and caching fixed-size chunks (4 MB by default in `earthaccess`) so nearby reads are served from memory instead of triggering new network requests.

## Virtual datasets and reference files

**VirtualiZarr**: a library that builds virtual Zarr datasets by referencing byte ranges within existing archival files (HDF5/NetCDF), without rewriting the data.

**Kerchunk**: the earlier/underlying reference-generation approach VirtualiZarr builds on; stores byte-range references as JSON.

**Icechunk**: a transactional, versioned storage engine for Zarr, usable as an alternative reference store to Kerchunk's JSON.

## Cloud-native formats and protocols

**COG (Cloud-Optimized GeoTIFF)**: a GeoTIFF internally organized (tiled + overviews) for efficient partial/remote reads.

**VSI (GDAL Virtual File System)**: GDAL's abstraction (`/vsicurl/`, `/vsis3/`) that lets GDAL-based tools read remote files as if they were local.

**OPeNDAP**: a data access protocol where the server performs subsetting, so the client only requests the slice it needs.

## Latency

**TTFB / TTS (Time to First Byte / Time to Science)**: informal terms for how long it takes to get usable data back, used to compare download vs. streaming latency.
