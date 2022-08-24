# Changelog

## [Unreleased]

* improved documentation:
    * all the underlaying methods are reimplemented for docstring compatibility

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

[Unreleased]: https://github.com/betolink/earthdata/compare/v0.3.0...HEAD
[v0.3.0]: https://github.com/betolink/earthdata/releases/tag/v0.3.0
[v0.2.2]: https://github.com/betolink/earthdata/releases/tag/v0.2.2
[v0.2.1]: https://github.com/betolink/earthdata/releases/tag/v0.2.1
[v0.1.0-beta.1]: https://github.com/betolink/earthdata/releases/tag/v0.1.0-beta.1
