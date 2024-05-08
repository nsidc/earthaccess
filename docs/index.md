# What is `earthaccess`?

`earthaccess` is a python library to **search for**, and **download** or **stream** NASA Earth science data with just a few lines of code.

Open science only reaches its full potential if we have easy-to-use workflows that facilitate research in an inclusive, efficient and reproducible way. Unfortunately —as it stands today— scientists and students alike face a steep learning curve adapting to systems that have grown too complex and end up spending more time on the technicalities of the tools, cloud and NASA APIs than focusing on their important science.

During several workshops organized by [NASA Openscapes](https://nasa-openscapes.github.io/events.html), the need to provide easy-to-use tools to our users became evident. Open science is a collaborative effort; it involves people from different technical backgrounds, and the data analysis to solve the pressing problems we face cannot be limited by the complexity of the underlying systems. Therefore, providing easy access to NASA Earthdata regardless of the data storage location (hosted within or outside of the cloud) is the main motivation behind this Python library.

The library is an open source community effort under an [MIT license](LICENSE.txt).  We welcome contributions to improve `earthaccess`.  Please see the [Contributing Guide](contributing/index.md) to learn how to get involved.

***earthaccess*** handles authentication with [NASA's Earthdata Login (EDL)](https://urs.earthdata.nasa.gov), search using NASA's [CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html) and access through [`fsspec`](https://github.com/fsspec/filesystem_spec).
