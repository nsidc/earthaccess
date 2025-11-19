# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Common Changelog](https://common-changelog.org/)
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added methods `doi` and `citation` to `DataCollection` class.
  ([#203](https://github.com/nsidc/earthaccess/issues/203))
  (@Sherwin-14, @chuckwondo)

### Removed

- **Breaking:** Remove _default automatic login_ behavior.  This removes
  previously undocumented behavior, where a user would be logged in
  automatically (i.e., without having to call `earthdata.login` explicitly) if
  the user had valid EDL credentials specified either via environment variables
  or a `netrc` file.  This led to potentially unexpected behavior.

  Removing this automatic behavior breaks existing user code that does not make
  an explicit call to `earthdata.login` before streaming/downloading data, but
  used to succeed due to the (perhaps unknown) automatic login behavior.

  Users must now _explicitly_ call `earthdata.login` in order to access data
  that requires EDL authentication.

  Removing this automatic behavior was necessary to fix
  [#945](https://github.com/nsidc/earthaccess/issues/945).

### Fixed

- Ignore environment variables `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`
  when `EARTHDATA_TOKEN` is set
  ([#1121](https://github.com/nsidc/earthaccess/issues/1121)) (@chuckwondo)
- Use only specified login strategy to attempt login, when strategy other than
  "all" is specified ([#945](https://github.com/nsidc/earthaccess/issues/945))
  (@chuckwondo)
- Fix undesirable pre-commit changes when running on Windows
  ([#1143](https://github.com/nsidc/earthaccess/issues/1143)) (@ana-sher)

## [0.15.1] - 2025-09-16

### Fixed

- Obstore and VirtualiZarr should not be required
  ([#1097](https://github.com/nsidc/earthaccess/issues/1097))
  ([@betolink](https://github.com/betolink))

## [0.15.0] - 2025-09-16

### Changed

- Populated glossary section under USER-REFERENCE.
  ([#1027](https://github.com/nsidc/earthaccess/issues/1027))
  ([@Sherwin-14](https://github.com/Sherwin-14))
- Change default cache behavior in fsspec from `readahead` to `blockcache`.
  Allow user defined config with `open_kwargs` in the `.open()` method.  This
  improves performance by an order of magnitude.
  ([#251](https://github.com/nsidc/earthaccess/discussions/251))
  ([#771](https://github.com/nsidc/earthaccess/discussions/771))
  ([@betolink](https://github.com/betolink))
- Add `show_progress` argument to `earthaccess.download()` to let the user
  control display of progress bars.  Defaults to true for interactive sessions,
  otherwise false.  ([#612](https://github.com/nsidc/earthaccess/issues/612))
  ([#1065](https://github.com/nsidc/earthaccess/pull/1065))
  ([@Sherwin-14](https://github.com/Sherwin-14))
- Updated bug and triage label names in bug Issue template.
  ([#998](https://github.com/nsidc/earthaccess/pull/998))
  ([@asteiker](https://github.com/asteiker))
- `download` now raises `DownloadFailure` exception on failure.
  ([#612](https://github.com/nsidc/earthaccess/issues/612))
  ([@Sherwin-14](https://github.com/Sherwin-14))
- `GESDISC` should be `GES_DISC` in docstrings.
  ([#1037](https://github.com/nsidc/earthaccess/issues/1037))
  ([@abarciauskas-bgse](https://github.com/abarciauskas-bgse))
- `open_virtual_mfdataset` now uses `virtualizarr` v2, and `obstore` in place of
  `fsspec`.  Updated Zarr to V3 xref #967.
  ([#1074](https://github.com/nsidc/earthaccess/issues/1074))
  ([@owenlittlejohns](https://github.com/owenlittlejohns))
- Populate search and access user guides.
  ([#1035](https://github.com/nsidc/earthaccess/pull/1035))
  ([@andypbarrett](https://github.com/andypbarrett))

### Added

- Added `tenacity` to retry downloads up to 3 times with exponential backoff time, replaces #1016
  ([#481](https://github.com/nsidc/earthaccess/issues/481))
  ([@betolink](https://github.com/betolink))
- Add notebook demonstrating workflow with TEMPO Level 3 data as a virtual dataset
  ([#924](https://github.com/nsidc/earthaccess/pull/924))
  ([@danielfromearth](https://github.com/danielfromearth))
- `get_s3_filesystem` now accepts an `endpoint` argument for specifying a credentials url.
  ([#602](https://github.com/nsidc/earthaccess/issues/602))
  ([@rwegener2](https://github.com/rwegener2))
- s3 `download` now checks for existing files.
  ([#807](https://github.com/nsidc/earthaccess/issues/807))
  ([@Sherwin-14](https://github.com/Sherwin-14))
- Added triaging guide ([#754](https://github.com/nsidc/earthaccess/issues/754))
  ([@Sherwin-14](https://github.com/Sherwin-14))
  ([@mfisher87](https://github.com/mfisher87))
- `download` now returns Path consistently.
  ([#595])(<https://github.com/nsidc/earthaccess/issues/595>)
  ([@Sherwin-14](https://github.com/Sherwin-14))
- Users may now authenticate with an existing Earthdata login token with
  environment variable `EARTHDATA_TOKEN`
  ([#484](https://github.com/nsidc/earthaccess/issues/484))
  ([@kgrimes2](https://github.com/kgrimes2))
- Added top level `status` function to check the statuses of NASA Earthdata services
  ([#161](https://github.com/nsidc/earthaccess/issues/161))
  ([@Sherwin-14](https://github.com/Sherwin-14))

### Removed

- **Breaking:** Removed `has_granules=true` and `include_granule_counts=true`
  as default parameters upon creation of a `DataCollections` instance.
  ([#884](https://github.com/nsidc/earthaccess/issues/884))
  ([@Sherwin-14](https://github.com/Sherwin-14))
- Python 3.10 is no longer supported.
  ([#966](https://github.com/nsidc/earthaccess/pull/966))
  ([@weiji14](https://github.com/weiji14))

### Fixed

- Files can be downloaded in the cloud([#1009](https://github.com/nsidc/earthaccess/issues/1009))([@betolink](https://github.com/betolink))
- Corrected Harmony typo in notebooks/Demo.ipynb([#995](https://github.com/nsidc/earthaccess/issues/995))([@stelios-c](https://github.com/stelios-c))
- Resolved an error in virtual dataset tutorial notebook ([#1044](https://github.com/nsidc/earthaccess/issues/1044))([@danielfromearth](https://github.com/danielfromearth))
- Issue when `FileDistributionInformation` did not exist for a collection
  ([#971](https://github.com/nsidc/earthaccess/pull/971))
  ([@mike-gangl](https://github.com/mike-gangl/))
- Reflected new publisher of SEDAC datasets ([#1032](https://github.com/nsidc/earthaccess/issues/1032))([@itcarroll](https://github.com/itcarroll))
- Better proxying by `EarthAccessFile` with correct MRO ([#610](https://github.com/nsidc/earthaccess/issues/610))([@alexandervladsemenov](https://github.com/alexandervladsemenov), [@itcarroll](https://github.com/itcarroll))

## [0.14.0] - 2025-02-11

### Added

- `search_datasets` now accepts a `has_granules` keyword argument. Use
  `has_granules=False` to search for metadata about collections with no
  associated granules. The default value set in `DataCollections` remains `True`.
  ([#939](https://github.com/nsidc/earthaccess/issues/939))
  ([**@juliacollins**](https://github.com/juliacollins))

### Changed

- **Breaking**: earthaccess will now raise an exception when login credentials are
  rejected.  If you need the old behavior, please use a `try` block.
  ([#946](https://github.com/nsidc/earthaccess/pull/946))
  ([**@mfisher87**](https://github.com/mfisher87), [@chuckwondo](https://github.com/chuckwondo),
  and [@jhkennedy](https://github.com/jhkennedy))

## [0.13.0] - 2025-01-28

### Added

- VirtualiZarr: earthaccess can open archival formats (NetCDF, HDF5) as if they were Zarr by leveraging VirtualiZarr
  In order to use this capability the collection needs to be supported by OPeNDAP and have dmrpp files.
  See [example notebooks](https://github.com/nsidc/earthaccess/blob/main/docs/tutorials/dmrpp-virtualizarr.ipynb)!
  ([**@ayushnag**](https://github.com/ayushnag) and [**@TomNicholas**](https://github.com/TomNicholas/))

### Fixed

- `earthaccess.download` will let requests automatically decode compressed content
  ([#887](https://github.com/nsidc/earthaccess/issues/887))
  ([**@itcarroll**](https://github.com/itcarroll))

- `earthaccess.download` now shares the authenticated session cookie among threads to avoid overloading EDL.
  ([#913](https://github.com/nsidc/earthaccess/issues/913))
  ([**@hailiangzhang**](https://github.com/hailiangzhang))

## [0.12.0] - 2024-11-13

### Changed

- Refactored our development guide to clarify development environment setup and how to run tests
  ([@jhkennedy](https://github.com/jhkennedy))
- Use built-in `assert` statements instead of `unittest` assertions in
  integration tests ([#743](https://github.com/nsidc/earthaccess/issues/743))
  ([@chuckwondo](https://github.com/chuckwondo))

### Added

- Add support for opening data files with virtualizarr and NASA dmrpp with `open_virtual_dataset`
  ([#605](https://github.com/nsidc/earthaccess/issues/605))
  ([@ayushnag](https://github.com/ayushnag))
- Add support for `NETRC` environment variable to override default `.netrc` file
  location ([#480](https://github.com/nsidc/earthaccess/issues/480))
  ([@chuckwondo](https://github.com/chuckwondo))
- Add `nox` session for running integration tests locally
  ([#815](https://github.com/nsidc/earthaccess/issues/815); [@chuckwondo](https://github.com/chuckwondo) and ([#872](https://github.com/nsidc/earthaccess/issues/872); [@jhkennedy](https://github.com/jhkennedy))
- Auto-add comment to PR that requires maintainer to review and re-run
  integration tests ([#824](https://github.com/nsidc/earthaccess/issues/824))
  ([@chuckwondo](https://github.com/chuckwondo))
- Add authentication to User Guide documentation. ([#763](https://github.com/nsidc/earthaccess/pull/763)) ([@andypbarrett](https://github.com/andypbarrett))

### Removed

- The `scripts/integration-test.sh` script has been removed in favor of the `integration-tests` nox session.
  ([#872](https://github.com/nsidc/earthaccess/issues/872)) ([@jhkennedy](https://github.com/jhkennedy))
- Python 3.9 is no longer supported.
  ([#876](https://github.com/nsidc/earthaccess/pull/876))
  ([@mfisher87](https://github.com/mfisher87))

### Fixed

- `earthaccess.download` will not ignore errors by default
  ([#581](https://github.com/nsidc/earthaccess/issues/581))
  ([**@Sherwin-14**](https://github.com/Sherwin-14),
  [**@chuckwondo**](https://github.com/chuckwondo),
  [**@mfisher87**](https://github.com/mfisher87))
- Integration tests no longer clobber existing `.netrc` file
  ([#806](https://github.com/nsidc/earthaccess/issues/806))
  (@chuckwondo)
- Return an empty list instead of raising an `IndexError` when searches find no results.
  ([#526](https://github.com/nsidc/earthaccess/issues/526))
  ([@jhkennedy](https://github.com/jhkennedy))

## [0.11.0] 2024-10-01

### Changed

- Automatically refresh EDL token and deprecate the `Auth.refresh_tokens` method
  with no replacement, as there is no longer a need to explicitly refresh
  ([#484](https://github.com/nsidc/earthaccess/issues/484))
  ([@fwfichtner](https://github.com/fwfichtner))
- Deprecate `earthaccess.get_s3fs_session` and `Store.get_s3fs_session`.  Use
  `earthaccess.get_s3_filesystem` and `Store.get_s3_filesystem`, respectively,
  instead ([#766](https://github.com/nsidc/earthaccess/issues/766))
  ([@Sherwin-14](https://github.com/Sherwin-14),
  [@chuckwondo](https://github.com/chuckwondo))

### Added

- Add Issue Templates ([#281](https://github.com/nsidc/earthaccess/issues/281))
  ([@Sherwin-14](https://github.com/Sherwin-14))
- Support Service queries
  ([#447](https://github.com/nsidc/earthaccess/issues/447))
  ([@nikki-t](https://github.com/nikki-t),
  [@chuckwondo](https://github.com/chuckwondo),
  [@mfisher87](https://github.com/mfisher87),
  [@betolink](https://github.com/betolink))
- Add example PR links to pull request template
  ([#756](https://github.com/nsidc/earthaccess/issues/756))
  ([@Sherwin-14](https://github.com/Sherwin-14),
  [@mfisher87](https://github.com/mfisher87))
- Add Contributing Naming Convention document
  ([#532](https://github.com/nsidc/earthaccess/issues/532))
  ([@Sherwin-14](https://github.com/Sherwin-14),
  [@mfisher87](https://github.com/mfisher87))

### Removed

- Remove `binder/` directory, as we no longer need a special
  [binder](https://mybinder.org) environment with the top-level
  `environment.yml` introduced in
  [#733](https://github.com/nsidc/earthaccess/issues/733)
  ([@jhkennedy](https://github.com/jhkennedy))

### Fixed

- Remove broken link "Introduction to NASA earthaccess"
  ([#779](https://github.com/nsidc/earthaccess/issues/779))
  ([@Sherwin-14](https://github.com/Sherwin-14))
- Restore automation for tidying notebooks used in documentation
  ([#788](https://github.com/nsidc/earthaccess/issues/788))
  ([@itcarroll](https://github.com/itcarroll))
- Remove the base class on `EarthAccessFile` to fix method resolution
  ([#610](https://github.com/nsidc/earthaccess/issues/610))
  ([@itcarroll](https://github.com/itcarroll))

## [0.10.0] 2024-07-19

### Changed

- Perform YAML formatting with `yamlfmt` instead of `prettier`
  ([#555](https://github.com/nsidc/earthaccess/issues/555))
  ([@chuckwondo](https://github.com/chuckwondo),
  [@mfisher87](https://github.com/mfisher87))
- Replace `print` calls with `logging` calls where appropriate and add T20 Ruff
  rule ([#511](https://github.com/nsidc/earthaccess/issues/511))
  ([@botanical](https://github.com/botanical),
  [@chuckwondo](https://github.com/chuckwondo),
  [@mfisher87](https://github.com/mfisher87))
- Update `CHANGELOG.md` to follow Common Changelog conventions
  ([#584](https://github.com/nsidc/earthaccess/pull/584))
  ([@danielfromearth](https://github.com/danielfromearth),
  [@chuckwondo](https://github.com/chuckwondo),
  [@jhkennedy](https://github.com/jhkennedy),
  [@mfisher87](https://github.com/mfisher87))

### Added

- Enable queries to Earthdata User Acceptance Testing (UAT) system for
  authenticated accounts
  ([#421](https://github.com/nsidc/earthaccess/issues/421))
  ([@danielfromearth](https://github.com/danielfromearth),
  [@mfisher87](https://github.com/mfisher87),
  [@jhkennedy](https://github.com/jhkennedy),
  [@chuckwondo](https://github.com/chuckwondo),
  [@betolink](https://github.com/betolink))
- Add support for Python 3.12
  ([#457](https://github.com/nsidc/earthaccess/issues/457))
  ([@chuckwondo](https://github.com/chuckwondo),
  [@mfisher87](https://github.com/mfisher87))
- Added documentation for the backwards compatibility
  ([#471](https://github.com/nsidc/earthaccess/issues/471))
  ([@Sherwin-14](https://github.com/Sherwin-14),
  [@mfisher87](https://github.com/mfisher87))

### Removed

- **Breaking:** Remove support for Python 3.8
  ([#457](https://github.com/nsidc/earthaccess/issues/457))
  ([@mfisher87](https://github.com/mfisher87),
  [@chuckwondo](https://github.com/chuckwondo))
- **Breaking:** Remove the `get_user_profile` method and the `email_address` and
  `profile` attributes from the `Auth` class.  Calling the EDL API to get user
  profile information is not intended for library access and is not necessary
  for this library's intended use cases.
  ([#421](https://github.com/nsidc/earthaccess/issues/421))
  ([@danielfromearth](https://github.com/danielfromearth),
  [@mfisher87](https://github.com/mfisher87),
  [@jhkennedy](https://github.com/jhkennedy),
  [@chuckwondo](https://github.com/chuckwondo),
  [@betolink](https://github.com/betolink))

### Fixed

- Use
  [Search After](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#search-after)
  for collection and granule searches to support deep-paging through large
  result sets ([#483](https://github.com/nsidc/earthaccess/issues/483))
  ([@doug-newman-nasa](https://github.com/doug-newman-nasa),
  [@chuckwondo](https://github.com/chuckwondo),
  [@mfisher87](https://github.com/mfisher87),
  [@betolink](https://github.com/betolink))
- Correct and enhance static type hints for functions and methods that make CMR
  queries or handle CMR query results
  ([#508](https://github.com/nsidc/earthaccess/issues/508))
  ([@mfisher87](https://github.com/mfisher87),
  [@jhkennedy](https://github.com/jhkennedy),
  [@chuckwondo](https://github.com/chuckwondo),
  [@betolink](https://github.com/betolink))
- Create destination path prior to direct S3 downloads, if it doesn't already
  exist ([#562](https://github.com/nsidc/earthaccess/issues/562))
  ([@itcarroll](https://github.com/itcarroll),
  [@mfisher87](https://github.com/mfisher87),
  [@chuckwondo](https://github.com/chuckwondo))
- Fix broken image link in sea level rise tutorial
  ([#427](https://github.com/nsidc/earthaccess/issues/427))
  ([@jbrownrs](https://github.com/jbrownrs))

## [0.9.0] - 2024-02-28

### Added

- Improve search by adding instrument and project to collection queries
  ([#427](https://github.com/nsidc/earthaccess/issues/427))
  ([@betolink](https://github.com/betolink),
  [@mfisher87](https://github.com/mfisher87),
  [@jhkennedy](https://github.com/jhkennedy))
- Add user-agent in the request to track usage
  ([#436](https://github.com/nsidc/earthaccess/issues/436))
  ([@asteiker](https://github.com/asteiker),
  [@@mikedorfman](https://github.com/@mikedorfman),
  [@betolink](https://github.com/betolink))

### Fixed

- Implement more trusted domains in the SessionWithRedirection
  ([#439](https://github.com/nsidc/earthaccess/issues/439))
  ([@cmspeed](https://github.com/cmspeed),
  [@mfisher87](https://github.com/mfisher87),
  [@betolink](https://github.com/betolink),
  [@jhkennedy](https://github.com/jhkennedy))
- Use an authenticated session for hits() instead of calling parent's class
  super() ([#438](https://github.com/nsidc/earthaccess/issues/438))
  ([@betolink](https://github.com/betolink),
  [@mfisher87](https://github.com/mfisher87),
  [@jhkennedy](https://github.com/jhkennedy))

## [0.8.2] - 2023-12-06

### Changed

- Update poetry lockfile
  ([#403](https://github.com/nsidc/earthaccess/pull/403))
  ([@jrbourbeau](https://github.com/jrbourbeau))
- Use YAML formatting (prettier)
  ([#398](https://github.com/nsidc/earthaccess/pull/398))
  ([@jrbourbeau](https://github.com/jrbourbeau))

### Added

- Add CI tests with minimum supported versions
  ([#402](https://github.com/nsidc/earthaccess/pull/402))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87),
  [@jhkennedy](https://github.com/jhkennedy))
- Add `python-dateutil` as a direct dependency
  ([#397](https://github.com/nsidc/earthaccess/pull/397))
  ([@jrbourbeau](https://github.com/jrbourbeau))

### Removed

- Remove binder PR comments
  ([#400](https://github.com/nsidc/earthaccess/pull/400))
  ([@jrbourbeau](https://github.com/jrbourbeau))

### Fixed

- Enable AWS check with IMDSv2
  ([#391](https://github.com/nsidc/earthaccess/pull/391))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87),
  [@itcarroll](https://github.com/itcarroll))
- Add region to running in AWS check
  ([#395](https://github.com/nsidc/earthaccess/pull/395))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@betolink](https://github.com/betolink))
- Handle opening multi-file granules
  ([#394](https://github.com/nsidc/earthaccess/pull/394))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@betolink](https://github.com/betolink))

## [0.8.1] - 2023-12-01

### Changed

- Handle S3 credential expiration more gracefully
  ([#354](https://github.com/nsidc/earthaccess/pull/354))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87))
- Use dependabot to update GitHub Actions
  ([#373](https://github.com/nsidc/earthaccess/pull/373))
  ([@jhkennedy](https://github.com/jhkennedy))
- Consolidate dependabot updates
  ([#380](https://github.com/nsidc/earthaccess/pull/380))
  ([@mfisher87](https://github.com/mfisher87))
- Switch to `ruff` for formatting
  ([#372](https://github.com/nsidc/earthaccess/pull/372))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87))

### Added

- Add `kerchunk` metadata consolidation utility
  ([#278](https://github.com/nsidc/earthaccess/pull/278))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87),
  [@betolink](https://github.com/betolink),
  [@martindurant](https://github.com/martindurant),
  [@lsterzinger](https://github.com/lsterzinger),
  [@mrocklin](https://github.com/mrocklin))

## [0.8.0] - 2023-11-29

### Changed

- Raise errors instead of `print`ing them in more cases
  ([#351](https://github.com/nsidc/earthaccess/pull/351))
  ([@jrbourbeau](https://github.com/jrbourbeau))
- `daac` and `provider` parameters are now normalized to uppercase, since
  lowercase characters are never valid
  ([#355](https://github.com/nsidc/earthaccess/pull/355))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87))
- Allow single file URL inputs for `earthaccess.download`
  ([#347](https://github.com/nsidc/earthaccess/pull/347))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87))

### Fixed

- Fix zero granules being reported for restricted datasets
  ([#358](https://github.com/nsidc/earthaccess/pull/358))
  ([@danielfromearth](https://github.com/danielfromearth))

## [0.7.1] - 2023-11-08

### Fixed

- Treat granules without `RelatedUrls` as not cloud-hosted
  ([#339](https://github.com/nsidc/earthaccess/pull/339))
  ([@mfisher87](https://github.com/mfisher87))

## [0.7.0] - 2023-10-31

### Changed

- `earthaccess.download` now accepts a single granule as input in addition to a
  list of granules ([#317](https://github.com/nsidc/earthaccess/pull/317))
  ([@jrbourbeau](https://github.com/jrbourbeau))
- `earthaccess.download` now returns fully qualified local file paths
  ([#317](https://github.com/nsidc/earthaccess/pull/317))
  ([@jrbourbeau](https://github.com/jrbourbeau))

### Added

- Earthaccess will now automatically search for Earthdata authentication.
  ``earthaccess.login()`` still works as before, but is no longer required if
  you have a ``~/.netrc`` file for have set ``EARTHDATA_USERNAME`` and
  ``EARTHDATA_PASSWORD`` environment variables
  ([#300](https://github.com/nsidc/earthaccess/pull/300))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87))
- Add `earthaccess.auth_environ()` utility for getting Earthdata authentication
  environment variables ([#316](https://github.com/nsidc/earthaccess/pull/316))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87))

### Fixed

- Fix spelling mistake in `access` variable assignment (`direc` -> `direct`) in
  `earthaccess.store._get_granules`
  ([#308](https://github.com/nsidc/earthaccess/pull/308))
  ([@trey-stafford](https://github.com/trey-stafford))
- Pass `threads` arg to `_open_urls_https` in `earthaccess.store._open_urls`,
  replacing the hard-coded value of 8
  ([#308](https://github.com/nsidc/earthaccess/pull/308))
  ([@trey-stafford](https://github.com/trey-stafford))
- Return S3 data links by default when in region
  ([#318](https://github.com/nsidc/earthaccess/pull/318))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mfisher87](https://github.com/mfisher87),
  [@jhkennedy](https://github.com/jhkennedy))

## [0.6.0] - 2023-09-20

### Added

- `earthaccess.get_s3fs_session()` can use the results to find the right set of
  S3 credentials ([#296](https://github.com/nsidc/earthaccess/pull/296))
  ([@betolink](https://github.com/betolink))

### Fixed

- `earthaccess.search_datasets()` and `earthaccess.search_data()` can find
  restricted datasets ([#296](https://github.com/nsidc/earthaccess/pull/296))
  ([@betolink](https://github.com/betolink))
- Fix distributed serialization for EarthAccessFile
  ([#301](https://github.com/nsidc/earthaccess/pull/301))
  ([@jrbourbeau](https://github.com/jrbourbeau)) and
  ([#276](https://github.com/nsidc/earthaccess/pull/276))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@betolink](https://github.com/betolink))

## [0.5.3] - 2023-08-01

### Added

- Add download from onprem how-to
  ([#265](https://github.com/nsidc/earthaccess/pull/265))
  ([@andypbarrett](https://github.com/andypbarrett))

### Changed

- For CI, integration tests are now only run when we push to main (after a
  merge) ([#267](https://github.com/nsidc/earthaccess/pull/267))
  ([@betolink](https://github.com/betolink))
- For CI, unit tests are run for any branch and opened PR
  ([#267](https://github.com/nsidc/earthaccess/pull/267))
  ([@betolink](https://github.com/betolink))
- Update example in `search_datasets`
  ([#247](https://github.com/nsidc/earthaccess/pull/247))
  ([@jrbourbeau](https://github.com/jrbourbeau))
- Improve remote cluster performance
  ([#259](https://github.com/nsidc/earthaccess/pull/259))
  ([@jrbourbeau](https://github.com/jrbourbeau),
  [@mrocklin](https://github.com/mrocklin),
  [@mfisher87](https://github.com/mfisher87))
- Return useful error message for failed download
  ([#263](https://github.com/nsidc/earthaccess/pull/263))
  ([@andypbarrett](https://github.com/andypbarrett))

### Fixed

- Granule's size() returned zero
  ([#267](https://github.com/nsidc/earthaccess/pull/267))
  ([@betolink](https://github.com/betolink))
- Add exception handling for fsspec sessions, thanks to @jrbourbeau
  ([#249](https://github.com/nsidc/earthaccess/pull/249))
  ([@jrbourbeau](https://github.com/jrbourbeau))

## [0.5.2] - 2023-04-21

### Removed

- Remove Benedict (core dependency) as the default dict for JSON coming from CMR
  ([#229](https://github.com/nsidc/earthaccess/pull/229),
  [#230](https://github.com/nsidc/earthaccess/issues/230))
  ([@psarka](https://github.com/psarka))

### Fixed

- S3 credentials endpoints are tried with tokens and basic auth until all the
  DAACs accept the same auth
  ([#234](https://github.com/nsidc/earthaccess/pull/234))
  ([@betolink](https://github.com/betolink))

## [0.5.1] - 2023-03-20

### Changed

- For CI, documentation for readthedocs fixed by including poetry as the default
  tool ([#214](https://github.com/nsidc/earthaccess/pull/214))
  ([@betolink](https://github.com/betolink))
- For CI, injected new secrets to test Auth using the icepyx convention
  (EARTHDATA_USERNAME) ([#214](https://github.com/nsidc/earthaccess/pull/214))
  ([@JessicaS11](https://github.com/JessicaS11),
  [@betolink](https://github.com/betolink))

### Added

- Add ability to get the user's profile with auth.user_profile which includes
  the user email ([#214](https://github.com/nsidc/earthaccess/pull/214))
  ([@betolink](https://github.com/betolink))
- Add LAAD as a supported DAAC
  ([#214](https://github.com/nsidc/earthaccess/pull/214))
  ([@betolink](https://github.com/betolink))

### Removed

- Remove magic from dependencies (not available in windows and not used but just
  in tests) ([#214](https://github.com/nsidc/earthaccess/pull/214))
  ([@betolink](https://github.com/betolink))

### Fixed

- `get_s3_credentials()` only worked when a netrc file was present, bug reported
  by @scottyhq and @JessicaS11
  ([#214](https://github.com/nsidc/earthaccess/pull/214))
  ([@betolink](https://github.com/betolink),
  [@JessicaS11](https://github.com/JessicaS11),
  [@scottyhq](https://github.com/scottyhq))
- Include tests for all DAAC S3 endpoints
  ([#214](https://github.com/nsidc/earthaccess/pull/214))
  ([@betolink](https://github.com/betolink))
- Update notebooks to use the new top level API
  ([#214](https://github.com/nsidc/earthaccess/pull/214))
  ([@betolink](https://github.com/betolink))

## [0.5.0] - 2023-02-23

### Changed

- For CI, documentation is now only built for the main, dev and documentation
  branches ([#202](https://github.com/nsidc/earthaccess/pull/202))
  ([@betolink](https://github.com/betolink))
- For CI, notebooks are executed every time the documentation gets published!
  ([#202](https://github.com/nsidc/earthaccess/pull/202))
  ([@betolink](https://github.com/betolink),
  [@asteiker](https://github.com/asteiker))

### Added

- Add ability to use the top level API to get S3 credentials, authenticated
  fsspec and requests sessions!
  ([#202](https://github.com/nsidc/earthaccess/pull/202))
  ([@betolink](https://github.com/betolink))
- Make available ASF direct access for Sentinel1 products
  ([#202](https://github.com/nsidc/earthaccess/pull/202))
  ([@betolink](https://github.com/betolink))

### Fixed

- Fix a bug where the Auth class is invoked without the proper parameters
  ([#202](https://github.com/nsidc/earthaccess/pull/202))
  ([@JessicaS11](https://github.com/JessicaS11))
- Raise and exception if a user specifies the netrc strategy and there is no
  netrc ([#202](https://github.com/nsidc/earthaccess/pull/202))
  ([@betolink](https://github.com/betolink))
- S3 URLs broke the Store class when opened outside AWS
  ([#202](https://github.com/nsidc/earthaccess/pull/202))
  ([@betolink](https://github.com/betolink))
- Opening files using URLs was not working properly on AWS, thanks to @amfriesz
  for reporting it!  ([#202](https://github.com/nsidc/earthaccess/pull/202))
  ([@betolink](https://github.com/betolink),
  [@amfriesz](https://github.com/amfriesz))

## [0.4.7] - 2022-12-11

### Fixed

- Fix open() for direct access
  ([#186](https://github.com/nsidc/earthaccess/pull/186))
  ([@betolink](https://github.com/betolink))
- Move python-magic to the dev section because it is a test dependency
  ([#186](https://github.com/nsidc/earthaccess/pull/186))
  ([@betolink](https://github.com/betolink))
- Make minor edits in the README
  ([#186](https://github.com/nsidc/earthaccess/pull/186))
  ([@betolink](https://github.com/betolink))

## [0.4.6] - 2022-12-08

### Changed

- For CI, only run the publish workflow after a release on GitHub
  ([#183](https://github.com/nsidc/earthaccess/pull/183))
  ([@betolink](https://github.com/betolink))

### Added

- Add feature to search collections by DOI
  ([#183](https://github.com/nsidc/earthaccess/pull/183))
  ([@betolink](https://github.com/betolink))
- Add new API documentation and simplify notation to access data
  ([#183](https://github.com/nsidc/earthaccess/pull/183))
  ([@jroebuck932](https://github.com/jroebuck932))

## [0.4.1] - 2022-11-02

### Changed

- For CI, install Poetry using the new script
  ([#131](https://github.com/nsidc/earthaccess/pull/131))
  ([@betolink](https://github.com/betolink))
- For CI, change dependabot alerts to monthly
  ([#131](https://github.com/nsidc/earthaccess/pull/131))
  ([@betolink](https://github.com/betolink))
- Improve documentation by reimplementing python_cmr methods for docstring
  compatibility ([#131](https://github.com/nsidc/earthaccess/pull/131))
  ([@betolink](https://github.com/betolink))
- Use `CMR-Search-After`
  ([#145](https://github.com/nsidc/earthaccess/issues/145))
  ([@betolink](https://github.com/betolink))

### Added

- Add GES_DISC S3 endpoint
  ([#131](https://github.com/nsidc/earthaccess/pull/131))
  ([@betolink](https://github.com/betolink))
- Improve documentation by adding types to method signatures
  ([#131](https://github.com/nsidc/earthaccess/pull/131))
  ([@betolink](https://github.com/betolink))

## [0.4.0] - 2022-08-17

### Added

- Add store, auth to docs and update mkdocs config
  ([#119](https://github.com/nsidc/earthaccess/pull/119))
  ([@betolink](https://github.com/betolink))
- For `auth`, add the ability to persist credentials into a `.netrc` file
  ([#119](https://github.com/nsidc/earthaccess/pull/119))
  ([@betolink](https://github.com/betolink))
- For `store`, use fsspec s3fs for in cloud access and https sessions for out of
  region access ([#43](https://github.com/nsidc/earthaccess/issues/43))
  ([@betolink](https://github.com/betolink))
- For `store`, can open files with fsspec in and out of region (stream into
  xarray) ([#41](https://github.com/nsidc/earthaccess/issues/41))
  ([@betolink](https://github.com/betolink))

## [0.3.0] - 2022-04-28

### Changed

- Update python-cmr to NASA fork
  ([#75](https://github.com/nsidc/earthaccess/pull/75))
  ([@jhkennedy](https://github.com/jhkennedy))
- Drop unused `pydantic` dependency
  ([`5761548`](https://github.com/nsidc/earthaccess/pull/75/commits/5761548fcd8ba8733ce4f5ff9b8ce7967c3a8398))
  ([@jhkennedy](https://github.com/jhkennedy))
- Auth can refresh CMR tokens
  ([#82](https://github.com/nsidc/earthaccess/pull/82))
  ([@betolink](https://github.com/betolink))
- Verify git tag and poetry version are the same before publishing to PyPI

### Added

- Add documentation for readthedocs and GitHub
  ([#82](https://github.com/nsidc/earthaccess/pull/82))
  ([@betolink](https://github.com/betolink))

### Removed

- **Breaking**: Drop python 3.7 support
  ([#82](https://github.com/nsidc/earthaccess/pull/82))
  ([@betolink](https://github.com/betolink))

### Fixed

- Fix bug with CMR tokens
- Add missing `python-datutil` dependency
  ([`747e992`](https://github.com/nsidc/earthaccess/pull/75/commits/747e9926a5ab83d75bbf7f17d4c52f24b563147b))
  ([@jhkennedy](https://github.com/jhkennedy))

## [0.2.2] - 2022-03-23

### Fixed

- Fix store to download multi-file granules
  ([#73](https://github.com/nsidc/earthaccess/pull/73))
  ([@betolink](https://github.com/betolink))
- Fix granule formatting ([#73](https://github.com/nsidc/earthaccess/pull/73))
  ([@betolink](https://github.com/betolink))

## [0.2.1] - 2022-03-19

### Changed

- Rename Accessor to Store
  ([`4bd618d`](https://github.com/nsidc/earthaccess/pull/66/commits/4bd618d4d48c3cd256a077fb8329f40df2d5b7ff))
  ([@betolink](https://github.com/betolink))
- Relax dependency requirements
  ([`c9a5ed6`](https://github.com/nsidc/earthaccess/pull/66/commits/c9a5ed6b917435e7c4ece58485939065fa71cc8f))
  ([@betolink](https://github.com/betolink))
- Store can download plain links if they are on prem
  ([`92d2919`](https://github.com/nsidc/earthaccess/commit/92d291962e5b72b458c2971eae8a6b813d4bae39))
  ([@betolink](https://github.com/betolink))

## [0.1.0-beta.1] - 2021-09-21

_Conception!_

### Added

- Add basic classes to interact with NASA CMR, EDL and cloud access.
- Basic object formatting.

[0.1.0-beta.1]: https://github.com/betolink/earthaccess/releases/tag/v0.1.0-beta.1
[0.2.1]: https://github.com/betolink/earthaccess/releases/tag/v0.2.1
[0.2.2]: https://github.com/betolink/earthaccess/releases/tag/v0.2.2
[0.3.0]: https://github.com/betolink/earthaccess/releases/tag/v0.3.0
[0.4.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.4.1
[0.4.6]: https://github.com/nsidc/earthaccess/releases/tag/v0.4.6
[0.4.7]: https://github.com/nsidc/earthaccess/releases/tag/v0.4.7
[0.5.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.5.0
[0.5.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.5.1
[0.5.2]: https://github.com/nsidc/earthaccess/releases/tag/v0.5.2
[0.5.3]: https://github.com/nsidc/earthaccess/releases/tag/v0.5.3
[0.6.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.6.0
[0.7.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.7.0
[0.7.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.7.1
[0.8.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.8.0
[0.8.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.8.1
[0.8.2]: https://github.com/nsidc/earthaccess/releases/tag/v0.8.2
[0.9.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.9.0
[0.10.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.10.0
[0.11.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.11.0
[0.12.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.12.0
[0.13.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.13.0
[0.14.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.14.0
[0.15.0]: https://github.com/nsidc/earthaccess/releases/tag/v0.15.0
[0.15.1]: https://github.com/nsidc/earthaccess/releases/tag/v0.15.1
[Unreleased]: https://github.com/nsidc/earthaccess/compare/v0.15.1...HEAD
