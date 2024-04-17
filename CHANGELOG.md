# Changelog

## [Unreleased]
* Bug fixes:
    * fixed 483 by extracting a common CMR query method for collections and granules using SearchAfter header
    * Added VCR support for verifying the API call to CMR and the parsing of returned results without relying on CMR availability post development

* Enhancements:
  * Corrected and enhanced static type hints for functions and methods that make
    CMR queries or handle CMR query results (#508)

## [v0.9.0] 2024-02-28

* Bug fixes:
    * fixed #439 by implementing more trusted domains in the SessionWithRedirection
    * fixed #438 by using an authenticated session for hits()
* Enhancements:
    * addressing #427 by adding parameters to collection query
    * added user-agent in the request to track usage, closes #436

## [v0.8.2] 2023-12-06
* Bug fixes:
    * Enable AWS check with IMDSv2
    * Add region to running in AWS check
    * Handle opening multi-file granules
* Maintenance:
    * Add CI tests with minimum supported versions
    * Update poetry lockfile
    * Add `python-dateutil` as a direct dependency
    * Remove binder PR comments
    * Add YAML formatting (prettier)

## [v0.8.1] 2023-12-01
* New Features:
    * Add `kerchunk` metadata consolidation utility.
* Enhancements:
    * Handle S3 credential expiration more gracefully.
* Maintenanece:
    * Use dependabot to update Github Actions.
    * Consolidate dependabot updates.
    * Switch to `ruff` for formatting.

## [v0.8.0] 2023-11-29
* Bug fixes:
    * Fix zero granules being reported for restricted datasets.
* Enhancements:
    * earthaccess will `raise` errors instead of `print`ing them in more cases.
    * `daac` and `provider` parameters are now normalized to uppercase, since lowercase
      characters are never valid.

## [v0.7.1] 2023-11-08
* Bug Fixes:
    * Treat granules without `RelatedUrls` as not cloud-hosted.

## [v0.7.0] 2023-10-31
* Bug Fixes:
    * Fix spelling mistake in `access` variable assignment (`direc` -> `direct`)
      in `earthaccess.store._get_granules`.
    * Pass `threads` arg to `_open_urls_https` in
      `earthaccess.store._open_urls`, replacing the hard-coded value of 8.
    * Return S3 data links by default when in region.
* Enhancements:
    * `earthaccess.download` now accepts a single granule as input in addition to a list of granules.
    * `earthaccess.download` now returns fully qualified local file paths.
* New Features:
    * Earthaccess will now automatically search for Earthdata authentication. ``earthaccess.login()``
      still works as before, but is no longer required if you have a ``~/.netrc`` file for have set
      ``EARTHDATA_USERNAME`` and ``EARTHDATA_PASSWORD`` environment variables.
    * Add `earthaccess.auth_environ()` utility for getting Earthdata authentication environment variables.

## [v0.6.0] 2023-09-20
* bug fixes:
    * earthaccess.search_datasets() and earthaccess.search_data() can find restricted datasets #296
    * distributed serialization fixed for EarthAccessFile #301 and #276
* new features:
    * earthaccess.get_s3fs_session() can use the results to find the right set of S3 credentials

## [v0.5.3] 2023-08-01
* bug fixes:
    * granule's size() returned zero
    * Added exception handling for fsspec sessions, thanks to @jrbourbeau
* CI changes:
    * integration tests are now only run when we push to main (after a merge)
    * unit tests run for any branch and opened PR

## [v0.5.2] 2023-04-21
* bug fixes:
    * Fixing #230 by removing Benedict as the dict handler, thanks to @psarka!
    * S3 credential endpoints are tried woth tokens and basic auth until all the DAACs accept the same auth

* Core dependencies:
    * Removed Benedict as the default dict for JSON coming from CMR.

## [v0.5.1] 2023-03-20

* bug fixes:
    * get_s3_credentials() only worked when a netrc file was present, bug reported by @scottyhq and @JessicaS11
    * including tests for all DAAC S3 endpoints
    * Notebooks updated to use the new top level API
    * removed magic from dependencies (not available in windows and not used but just in tests)

* CI changes:
    * documentation for readthedocs fixed by including poetry as the default tool
    * injected new secrets to test Auth using the icepyx convention (EARTHDATA_USERNAME)
* New Features
    * we can get the user's profile with auth.user_profile which includes the user email
    * added LAAD as a supported DAAC
## [v0.5.0] 2023-02-23

* bug fixes:
    * @JessicaS11 fixed a bug where the Auth class was invoked without the proper parameters
    * if a user specifies the netrc strategy and there is no netrc an exception is raised
    * S3 URLs broke the Store class when opened outside AWS
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

[Unreleased]: https://github.com/nsidc/earthaccess/compare/v0.9.0...HEAD
[v0.8.2]: https://github.com/nsidc/earthaccess/releases/tag/v0.8.2
[v0.8.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.8.1
[v0.8.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.8.0
[v0.7.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.7.1
[v0.7.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.7.0
[v0.6.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.6.0
[v0.5.3]: https://github.com/nsidc/earthaccess/releases/tag/v0.5.3
[v0.5.2]: https://github.com/nsidc/earthaccess/releases/tag/v0.5.2
[v0.5.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.5.1
[v0.5.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.5.0
[v0.4.7]: https://github.com/nsidc/earthaccess/releases/tag/v0.4.7
[v0.4.6]: https://github.com/nsidc/earthaccess/releases/tag/v0.4.6
[v0.4.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.4.1
[v0.3.0]: https://github.com/betolink/earthaccess/releases/tag/v0.3.0
[v0.2.2]: https://github.com/betolink/earthaccess/releases/tag/v0.2.2
[v0.2.1]: https://github.com/betolink/earthaccess/releases/tag/v0.2.1
[v0.1.0-beta.1]: https://github.com/betolink/earthaccess/releases/tag/v0.1.0-beta.1
