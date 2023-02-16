# Changelog

## [UNRELEASED]

## [v0.5.0] 2023-02-16
* bug fixes:
    * @JessicaS11 fixed a bug where the Auth class was invoked without the proper parameters
    * if a user specifies the netrc strategy and there is no netrc an exception is raised
    * Opening files using URLs was not working properly on AWS, thanks to @amfriesz for reporting it! 
* CI changes:
    * documentation is now only built for the main, dev and documentation branches
    * noteboks are executed every time the documentation gets published!
* New features:
    * we can now use the top level API to get S3 credentials, authenticated fsspec and requests sessions!
    * ASF direct access for Sentinel1 products is now available

## [v0.4.7] 2022-12-11

* bug fixes:
    * fixed open() for direct access
    * python-magic is a test dependency so moved to the dev section.
    * Minor edits in the README

## [v0.4.6] 2022-12-08

* Features:
    * search collections by DOI
    * new API documentation and simplified notation to access data
* CI changes:
    * only run the publish workflow after a release on github

## [v0.4.1] 2022-11-02

* improved documentation:
    * reimplemented python_cmr methods for docstring compatibility
    * added types to method signatures
* Using `CMR-Search-After` see #145

* CI changes:
    * Poetry is installed using the new script
    * Dependabot alerts to monthly

* Added GES_DISC S3 endpoint

## [v0.4.0] 2022-08-17

* `store`
    * uses fsspec s3fs for in cloud access and https sessions for out of region access
    * we can open files with fsspec in and out of region (stream into xarray)
* `auth`
    * we can persist our credentials into a `.netrc` file

* Documentation
    * added store, auth to docs and updated mkdocs congif


## [v0.3.0] 2022-04-28

- Fixed bug with CMR tokens
- dropped python 3.7 support
- updated python-cmr to NASA fork
- added documentation for readthedocs and github
- verifying git tag and poetry version are the same before publish to pypi
- Auth can refresh CMR tokens
- Dropped unused `pydantic` dependency
- Added missing `python-datutil` dependency

## [v0.2.2] 2022-03-23
- Bug fixes to store to download multi-file granules
- Fix granule formatting

## [v0.2.1] 2022-03-19
- Renamed Accessor to Store
- relaxed dependency requirements
- Store can download plain links if they are on prem

## [v0.1.0-beta.1] - 2021-09-21

- Conception!
- Add basic classes to interact with NASA CMR, EDL and cloud access.
- Basic object formatting.

[Unreleased]: https://github.com/betolink/earthaccess/compare/v0.3.0...HEAD
[v0.3.0]: https://github.com/betolink/earthaccess/releases/tag/v0.3.0
[v0.2.2]: https://github.com/betolink/earthaccess/releases/tag/v0.2.2
[v0.2.1]: https://github.com/betolink/earthaccess/releases/tag/v0.2.1
[v0.1.0-beta.1]: https://github.com/betolink/earthaccess/releases/tag/v0.1.0-beta.1
