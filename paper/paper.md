---
title: 'earthaccess: A Python Library for Simplified Discovery and Access of NASA Earth Science Data'
tags:
  - Python
  - Earth science
  - remote sensing
  - data access
  - cloud computing
  - NASA
  - open science
authors:
  - given-names: "Andrew P."
    surname: "Barrett"
    orcid: "https://orcid.org/0000-0003-4394-5445"
    affiliation: "1"
  - given-names: "Chris"
    surname: "Battisto"
    orcid: "https://orcid.org/0000-0002-9608-3634"
    affiliation: "2"
  - given-names: "James"
    surname: "Bourbeau"
    orcid: "https://orcid.org/0000-0003-2164-7789"
    affiliation: "3"
  - given-names: "Ian"
    surname: "Carroll"
    orcid: "https://orcid.org/0000-0002-3616-810X"
    affiliation: "4, 13"
  - given-names: "Chuck"
    surname: "Daniels"
    affiliation: "5"
  - given-names: "Matt"
    surname: "Fisher"
    orcid: "https://orcid.org/0000-0003-3260-5445"
    affiliation: "6"
  - given-names: "Daniel E."
    surname: "Kaufman"
    orcid: "https://orcid.org/0000-0002-1487-7298"
    affiliation: "7, 8"
  - given-names: "Joseph H."
    surname: "Kennedy"
    orcid: "https://orcid.org/0000-0002-9348-693X"
    affiliation: "9"
  - given-names: "Luis"
    surname: "Lopez"
    orcid: "https://orcid.org/0000-0003-4896-3263"
    affiliation: "1"
  - given-names: "Julia S."
    surname: "Lowndes"
    orcid: "https://orcid.org/0000-0003-1682-3872"
    affiliation: "10"
  - given-names: "Jessica"
    surname: "Scheick"
    orcid: "https://orcid.org/0000-0002-3421-4459"
    affiliation: "11"
  - given-names: "Amy"
    surname: "Steiker"
    orcid: "https://orcid.org/0000-0002-3039-0260"
    affiliation: "1"
  - given-names: "Sherwin"
    surname: "Varghese"
    orcid: "https://orcid.org/0009-0005-7030-213X"
    affiliation: "12"
affiliations:
 - name: "National Snow and Ice Data Center (NSIDC), Cooperative Institute for Research in Environmental Sciences (CIRES), University of Colorado Boulder, Boulder, CO, USA"
   index: 1
   ror: 02s376052
 - name: "NASA Goddard Space Flight Center, Goddard Earth Sciences Data and Information Services Center (GES DISC), Greenbelt, MD, USA"
   index: 2
   ror: 0171mag52
 - name: "Coiled Computing, Inc."
   index: 3
 - name: "Ocean Ecology Lab, NASA Goddard Space Flight Center, Greenbelt, MD, USA"
   index: 4
   ror: 0171mag52
 - name: "Development Seed, Inc."
   index: 5
 - name: "Schmidt Center for Data Science and Environment (DSE), University of California Berkeley"
   index: 6
   ror: "01an7q238"
 - name: "NASA Langley Research Center, Atmospheric Science Data Center (ASDC), Hampton, VA, USA"
   index: 7
   ror: 0399mhs52
 - name: "Booz Allen Hamilton, Inc., McLean, VA, USA"
   index: 8
   ror: 051rcp357
 - name: "University of Alaska Fairbanks, Fairbanks, AK, USA"
   index: 9
   ror: 01j7nq853
 - name: "Openscapes and National Center for Ecological Analysis and Synthesis (NCEAS), University of California Santa Barbara, Santa Barbara, CA, USA"
   index: 10
   ror: 02t274463
 - name: "University of New Hampshire, Durham, NH, USA and eScience Institute, University of Washington, Seattle, WA, USA"
   index: 11
   ror: 02q4hks80
 - name: "Independent Contributor"
   index: 12
 - name: "GESTAR II, University of Maryland Baltimore County, Baltimore, MD, USA"
   index: 13
   ror: 02qskvh78
date: 05 March 2026
bibliography: paper.bib
---

# Summary

`earthaccess` is an open-source Python library that simplifies the discovery, authentication,
and access of NASA Earth science data. NASA's Earth Observing System Data and Information System
(EOSDIS) distributes over 100 petabytes of data across 12 Distributed Active Archive Centers
(DAACs) [@nasa_earthdata], encompassing satellite imagery, climate records, atmospheric
measurements, and other geospatial datasets critical to Earth science research. Accessing these
data programmatically has historically required researchers to navigate multiple authentication
systems, understand provider-specific APIs and protocols, and write substantial boilerplate code
-- challenges that particularly affect researchers without deep software engineering
experience.

`earthaccess` provides a unified, high-level Python interface that reduces this
workflow to just a few lines of code. The library handles authentication with NASA's
Earthdata Login (EDL) service [@nasa_edl], exposes NASA's Common Metadata Repository
(CMR) [@nasa_cmr] for data discovery, and transparently manages data retrieval via
either HTTPS download or direct S3 access when running in the Amazon Web Services (AWS)
`us-west-2` region -- where NASA's cloud-hosted data resides. `earthaccess` also supports
streaming data directly into analysis-ready formats using `fsspec` [@fsspec] and
constructing virtual Zarr stores from archival formats (e.g., HDF5 and NetCDF4) using
DMR++ metadata [@dmrpp], powered by VirtualiZarr [@virtualizarr] and kerchunk [@kerchunk].


# Statement of need

NASA's Earth science data archive is one of the largest and most diverse collections of
Earth observation data in the world, used by tens of thousands of researchers, educators,
and decision-makers globally. However, the complexity of the underlying data infrastructure
presents a significant barrier to scientific productivity. A typical data access workflow
requires a researcher to: (1) authenticate with NASA Earthdata Login; (2) discover
relevant datasets and granules through the CMR API; (3) parse metadata to obtain download
URLs; (4) manage HTTP sessions with tokens and redirect handling; (5) determine whether
data are hosted on-premises or in the Earthdata Cloud; and (6) obtain temporary AWS S3
credentials when accessing cloud-hosted data. Each step introduces opportunities for
error, and DAAC-specific configurations further compound the challenge.

NASA's ongoing migration to the Earthdata Cloud adds further complexity, as researchers
must now contend with two possible access paradigms (traditional HTTPS downloads and S3-based
access), and sometimes even within a single analysis workflow. During workshops organized by NASA
Openscapes [@nasa_openscapes; @lowndes2019], the need for simpler tools became evident.
`earthaccess` was created to address this gap: it provides uniform access to NASA
Earthdata regardless of data storage location, enabling researchers to focus on science
rather than data engineering.

The target audience includes Earth scientists, remote sensing researchers, climate modelers,
hydrologists, ecologists, and any researcher, application developer, or educator who needs
to work with NASA Earth science data. The library is designed to be approachable for those new to Python -- with a
three-step workflow of `login()`, `search_data()`, and `download()` -- while offering
sufficient depth for advanced users who need direct S3 access, streaming file handles,
or virtual dataset construction for large-scale analysis.


# State of the field

The scholarly contribution of `earthaccess` is the _integration_ of search,
authentication, and access into a coherent abstraction that masks the heterogeneity
of NASA's data infrastructure. No existing tool provides this end-to-end,
provider-agnostic workflow. Rather than reinventing query or filesystem libraries,
`earthaccess` composes and extends existing open-source tools and contributes the
NASA-specific domain knowledge (DAAC configurations, credential endpoints,
authentication flows, cloud-detection logic) that binds them into a usable
data access layer.

Several tools exist for accessing NASA Earth science data, each addressing a specific
slice of the workflow:

- **python-cmr** [@python_cmr] provides a Python wrapper around the CMR API for dataset
  and granule queries. `earthaccess` builds on `python-cmr`, extending it with
  DAAC-aware provider resolution, cloud-hosting filters, and rich result objects that
  encapsulate metadata. However, `python-cmr` does not handle authentication, data
  download, or cloud access -- the areas where researchers face many workflow difficulties.

- **harmony-py** [@harmony_py] is NASA's client for the Harmony data transformation
  service, which provides, for example, server-side subsetting, reformatting, and reprojection services.
  It addresses a complementary use case; `earthaccess` focuses on direct data access
  and client-side analysis.

- **icepyx** [@icepyx] provides specialized tools for ICESat-2 data, including
  subsetting and variable selection. It is mission-specific by design, whereas
  `earthaccess` is mission-agnostic and supports all EOSDIS data holdings.

- **earthdatalogin** [@earthdatalogin_r] provides similar authentication and access
  functionality for the R programming ecosystem. The two projects share a common motivation and
  serve as complementary tools for their respective language communities.

- **Direct use of `fsspec`/`s3fs`** [@fsspec; @s3fs]: Advanced users can compose their
  own access workflows using these general-purpose filesystem libraries. However, this
  requires extensive knowledge of NASA's authentication flow, DAAC-specific credential
  endpoints, and the mapping between on-premises and cloud-hosted data links.


# Software design

`earthaccess` is organized into four core layers, each encapsulating a distinct
concern of the data access workflow:

1. **Authentication**: Manages the full lifecycle of NASA Earthdata Login credentials,
   supporting environment variables, `.netrc` files, and interactive prompts. Once
   authenticated, the library creates HTTP sessions that correctly handle NASA's
   cross-domain redirects and retrieves temporary AWS S3 credentials for in-region
   cloud access.

2. **Search**: Extends `python-cmr` with DAAC-aware provider resolution, cloud-hosting
   detection, and deep-paging support. Query results are wrapped in rich objects that
   preserve the full metadata response while exposing convenience methods for data
   links, spatial footprints, and formatted citations.

3. **Access**: Detects at runtime whether the process is running within AWS `us-west-2`
   and automatically selects the optimal access path -- direct S3 reads for in-region
   access or HTTPS downloads otherwise. Files can be opened as `fsspec`-compatible
   file-like objects for streaming into libraries such as xarray [@xarray], or
   downloaded to disk with parallel, fault-tolerant transfers.

4. **Virtual datasets**: Leverages NASA's DMR++ sidecar metadata files [@dmrpp] to
   construct virtual Zarr stores via VirtualiZarr [@virtualizarr] or kerchunk
   [@kerchunk], enabling lazy, chunk-level access to archival HDF5/NetCDF4 data without downloading or reformatting files. For example, a researcher can extract a single variable across thousands of files by reading only the relevant byte ranges from NASA's cloud storage, with minimal local resource usage. These features are available as optional dependencies to keep the core library lightweight.

Several deliberate design decisions shape the library:

**Build on, don't replace, existing libraries.** `earthaccess` composes existing
open-source tools -- `python-cmr` for search, `fsspec` and `s3fs` for file I/O,
VirtualiZarr and kerchunk for virtual datasets -- rather than reimplementing their
functionality. The library's unique contribution is the NASA-specific integration
layer that binds these tools together.

**Contribute upstream, don't accumulate.** When community discussions surface
features that belong in a dependency, the project contributes that work upstream
rather than absorbing it. Advanced CMR query capabilities were developed in
`python-cmr` rather than duplicated in `earthaccess`, and aspects of DMR++ parsing and
multi-file virtual dataset functionality were migrated to VirtualiZarr where
they could benefit the wider community. This upstream-first discipline avoids
scope creep, reduces maintenance burden, and strengthens the broader ecosystem
that `earthaccess` depends on.

**Location-transparent access.** The same user code works whether the computation runs
in the cloud or on a local workstation. The library automatically selects the optimal
access path without requiring code changes, reflecting the reality that researchers
are at varying stages of cloud adoption.

**Flat, functional top-level API.** All primary operations are exposed as module-level
functions (e.g., `earthaccess.login()`, `earthaccess.search_data()`,
`earthaccess.download()`), minimizing conceptual overhead for new users while
keeping the underlying object-oriented classes accessible for advanced use cases.


# Research impact statement

`earthaccess` has established itself as foundational infrastructure for NASA Earth
science data access. Concrete evidence of its impact includes:

**Peer-reviewed publications.** `earthaccess` has been used in published research,
including studies on multi-sensor drought observations in forested environments
[@andreadis2024] and tidal bore detection using SWOT satellite data [@arildsen2025].

**Community adoption.** The library is a dependency of 230 public GitHub
repositories (as of 5 March 2026), spanning data analysis workflows, Jupyter-based tutorials, and
downstream libraries. It is distributed through both PyPI and conda-forge, and has
been installed and used in cloud-hosted Jupyter environments provided by NASA and
partner organizations. As one example of downstream adoption, icepack -- a finite
element library for ice sheet and glacier modeling [@shapero2021] -- replaced its
hand-written NSIDC data-fetching routines with `earthaccess` calls, eliminating
hard-coded URLs and custom authentication logic.

**Multi-institutional development.** Contributors span NASA's Distributed Active Archive Centers (DAACs) — including ASDC, ASF, GES DISC, LP DAAC, NSIDC, OB.DAAC, ORNL DAAC, and PO.DAAC — as well as other federal and academic institutions (USGS,
University of New Hampshire), private industry (Coiled, Development Seed),
and independent open-source contributors. This breadth reflects both the library's
relevance across domains and the health of its contributor community.

**Integration with the NASA ecosystem.** `earthaccess` is featured in official NASA
Earthdata tutorials including <https://www.earthdata.nasa.gov/data/tools/earthaccess>, has been presented at AGU Fall Meetings, and was the subject of
a NASA ESDS Tech Spotlight presentation. The documentation includes executable Jupyter
notebooks demonstrating workflows with ICESat-2, EMIT, TEMPO, SMAP, and other missions,
providing reproducible entry points for researchers.


# AI usage disclosure

No generative AI tools were used in the development of the earthaccess software; all architectural and design decisions were made exclusively by the authors and contributors.

Preparation of this manuscript was assisted by Claude [Sonnet 4.6 and Opus 4.6] (Anthropic), which was applied to the full manuscript using the repository source code, documentation, commit history, and project metadata as context. Assistance was used for manuscript drafting and editorial revision. All content was reviewed, revised, and verified for accuracy by the authors, who bear full responsibility for the submitted work.


# Acknowledgements

The development of `earthaccess` was supported by NASA's Earth Science Data Systems
(ESDS) program through the Openscapes project (NASA award **______**, PIs Julia
Lowndes and Erin Robinson). We thank NASA Openscapes for the community workshops, collaborative working environment, and people-first approach that have motivated and continue to support this work. We are grateful to the
National Snow and Ice Data Center (NSIDC) for hosting the repository during its initial
development, and to all contributors who have shaped `earthaccess` through code,
documentation, issue reports, and community engagement. People have been able to contribute to earthaccess as adopters and developers as part of their jobs across the NASA ecosystem as well as outside of it, and this has been critical to making this shared resource successful. We appreciate everyone who had advocated and approved time to make this possible. We also thank Allison Horst
for the `earthaccess` artwork.


# References
