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
    affiliation: "4, 14"
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
    affiliation: "11, 12"
  - given-names: "Amy"
    surname: "Steiker"
    orcid: "https://orcid.org/0000-0002-3039-0260"
    affiliation: "1"
  - given-names: "Sherwin"
    surname: "Varghese"
    orcid: "https://orcid.org/0009-0005-7030-213X"
    affiliation: "13"
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
 - name: "Development Seed"
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
 - name: "Alaska Satellite Facility, Geophysical Institute, University of Alaska Fairbanks, Fairbanks, AK, USA"
   index: 9
   ror: 01j7nq853
 - name: "Openscapes and National Center for Ecological Analysis and Synthesis (NCEAS), University of California Santa Barbara, Santa Barbara, CA, USA"
   index: 10
   ror: 02t274463
 - name: "University of New Hampshire, Durham, NH, USA"
   index: 11
   ror: 01rmh9n78
 - name: "eScience Institute, University of Washington, Seattle, WA, USA"
   index: 12
   ror: 00cvxb145
 - name: "Independent Contributor"
   index: 13
 - name: "GESTAR II, University of Maryland Baltimore County, Baltimore, MD, USA"
   index: 14
   ror: 02qskvh78
date: 04 September 2026
bibliography: paper.bib
---

# Summary

`earthaccess` is an open-source Python library that simplifies discovery,
authentication, and access of NASA Earth science data. NASA's Earth Observing System
Data and Information System (EOSDIS) distributes over 100 petabytes of data across 11
Distributed Active Archive Centers (DAACs) [@nasa_earthdata], encompassing satellite
imagery, climate records, atmospheric measurements, and other geospatial datasets
critical to Earth science research. Accessing these data programmatically has
historically required researchers to navigate multiple authentication systems,
understand provider-specific APIs and protocols, and write substantial boilerplate code
-- challenges that particularly deter researchers without deep software engineering
experience.

`earthaccess` provides a unified, high-level Python interface that simplifies this workflow
to just a few lines of code. The library handles authentication with NASA's Earthdata
Login (EDL) service [@nasa_edl], queries to NASA's Common Metadata Repository (CMR)
[@nasa_cmr] for data discovery, and data retrieval through a single interface
covering both HTTPS download and direct Amazon Web Services (AWS) S3 access. `earthaccess` also supports streaming data directly into
analysis-ready formats using `fsspec` [@fsspec] and constructing virtual Zarr stores
from archival formats (e.g., HDF5 and NetCDF4) using DMR++ metadata [@dmrpp] (powered by
`VirtualiZarr` [@virtualizarr] and `kerchunk` [@kerchunk]), enabling drastic
improvements in access performance.


# Statement of need

NASA's Earth science data archive is one of the largest and most diverse collections of
Earth observation data in the world, used by over ten million researchers, educators,
and decision-makers globally [@nasa_esds_data_metrics]. However, the complexity of the
underlying data infrastructure presents a significant barrier to scientific
productivity. A typical data access workflow requires a researcher to: (1) search the
CMR API to discover relevant datasets and products; (2) parse the returned metadata to
identify specific granules and extract the appropriate access URLs; (3) authenticate
with NASA Earthdata Login and maintain authenticated sessions that handle
cross-domain redirects; (4) for NASA Earth science data hosted in the same AWS region as
the researcher's compute environment, obtain and periodically renew temporary AWS S3
credentials; and (5) retrieve the data by downloading it over HTTPS, streaming it
directly from S3, or passing the information into a third-party package for
customization services. Researchers must know enough about the technical implementation
of multiple unique APIs to perform these steps accurately, each of which introduces
opportunities for error. DAAC-specific configurations and NASA's migration of data to
the Earthdata Cloud compound the challenge.

NASA's Earthdata Cloud introduced a novel source of complexity for most researchers, who
must now choose between two possible access paradigms: traditional HTTPS downloads and
S3-based access. These both may even occur within a single analysis workflow. During
workshops organized by NASA Openscapes [@nasa_openscapes; @lowndes2019], the need for
simpler tools became evident. `earthaccess` is a community project that was created to
address this gap: it provides a uniform interface for access to NASA Earthdata regardless of data
storage location and handles authentication, credentials, and tokening behind the
scenes, enabling researchers to focus more on scientific interpretation and discovery.
The target audience spans Earth system science — from atmospheric scientists and
oceanographers to ecologists and land surface modelers — as well as operational
communities such as weather forecasters and disaster response practitioners. It also
serves remote sensing researchers, application developers, educators, and
decision-makers who work with NASA Earth science data. The library is designed to be
approachable for those new to Python -- with a three-step workflow of `login()`,
`search_data()`, and `download()` -- while offering sufficient depth for advanced users
who need direct S3 access, streaming file handles, or virtual dataset construction for
large-scale analysis.


# State of the field

The scholarly contribution of `earthaccess` is the _integration_ of search,
authentication, and access into a coherent abstraction that masks the heterogeneity of
NASA Earthdata's infrastructure. No existing tool provides this end-to-end workflow across the full breadth of NASA Earthdata. Rather than reinventing query or filesystem libraries,
`earthaccess` composes and extends existing open-source tools and contributes the
NASA-specific domain knowledge (DAAC configurations, credential endpoints,
authentication flows, and the mapping between HTTPS and direct-S3 access links) that
binds them into a usable data access layer.

Several tools exist for accessing NASA Earth science data, each addressing only part of
the workflow, or addressing the full workflow for only a subset of NASA's data holdings:

- **python-cmr** [@python_cmr] handles the search step (1) by providing a Python wrapper
  around the CMR API for dataset and granule queries. `earthaccess` builds on
  `python-cmr`, extending it with DAAC-aware provider resolution, cloud-hosting filters,
  and rich result objects that encapsulate metadata (step 2). However, `python-cmr` does
  not handle authentication, data download, or cloud access (steps 3–5) -- the areas
  where researchers face many workflow difficulties.

- **asf_search** [@asf_search] sits between `python-cmr` and `earthaccess` in scope: it focuses
  on search and discovery but also handles authentication and access (workflow steps
  1–5). It emerged around the same time as `earthaccess`, from similar access
  challenges. Unlike `earthaccess`, which is mission- and domain-agnostic, `asf_search`
  is tailored to synthetic aperture radar (SAR) data, adding domain-specific tooling and
  functionality.

- **icepyx** [@icepyx] provides a mission-specific solution to the general problem
  solved by earthaccess: search, discovery, authentication, and access to ICESat-2
  [@icesat2] data products. Established about a year before earthaccess, it handles
  workflow steps 1, 2, and 5 on its own and now leverages earthaccess to
  authenticate when users perform an action that requires logging
  in.

- **earthdatalogin** [@earthdatalogin_r] provides similar authentication and access
  functionality (steps 3–5) for the R programming ecosystem. The two projects share a
  common motivation and serve as complementary tools for their respective language
  communities.

- **Direct use of `fsspec`/`s3fs`** [@fsspec; @s3fs]: Advanced users can compose their
  own access workflows (step 5) using these general-purpose filesystem libraries.
  However, this requires extensive knowledge of NASA's authentication flow,
  DAAC-specific credential endpoints, and the mapping between download versus
  cloud-streaming data access links.


# Software design

`earthaccess` is organized into four core components, each encapsulating a distinct
stage of the data access workflow:

- **Authentication**: Manages the lifecycle of NASA Earthdata Login credentials,
  supporting environment variables, `.netrc` files, and interactive prompts. Once
  authenticated, the library creates HTTP sessions that safely handle NASA's
  cross-domain redirects, and it retrieves and renews temporary AWS S3 credentials for
  direct S3 access.

- **Search**: Extends `python-cmr` with DAAC-aware provider resolution, cloud-hosting
  detection, and deep-paging support. Query results (powered by `python-cmr`) are wrapped in rich objects that
  preserve the full metadata response while exposing convenient accessors for data links,
  spatial footprints, and formatted citations.

- **Access**: Presents a single interface over both access mechanisms -- HTTPS and
  direct S3 reads -- so that the same user code works from a local workstation or from
  within AWS, with the mechanism selectable by the user. Files can be opened as
  `fsspec`-compatible file-like objects for streaming into libraries such as `xarray`
  [@xarray], or downloaded to disk with parallel, fault-tolerant transfers. Because
  `earthaccess` returns ordinary Python file-like objects and makes no assumptions about
  the underlying file format, it interoperates directly with the wider scientific Python
  ecosystem -- including the PyData and Pangeo tool stacks -- rather than requiring
  format- or mission-specific readers.

- **Virtual datasets**: Leverages NASA's DMR++ sidecar metadata files [@dmrpp] to
  construct virtual Zarr stores via `VirtualiZarr` [@virtualizarr] or `kerchunk`
  [@kerchunk], enabling lazy, chunk-level access to archival HDF5/NetCDF4 data without
  downloading or reformatting files. For example, a researcher can extract a single
  variable across thousands of files by reading only the relevant byte ranges from
  NASA's cloud storage, with minimal local resource usage. These features are available
  as optional dependencies to keep the core library lightweight.

Several deliberate design decisions shape the library:

**Build on existing libraries.** `earthaccess` composes existing
open-source tools -- `python-cmr` for search, `fsspec` and `s3fs` for file I/O,
`VirtualiZarr` and `kerchunk` for virtual datasets -- rather than reimplementing their
functionality. The library's unique contribution is the NASA-specific integration layer
that binds these tools together. For example, retrieving NASA's TEMPO Level-3 ozone
product [@tempo_o3tot_l3] directly from the Earthdata Cloud with `boto3`, `requests`,
and `s3fs` requires about two dozen lines of code (excluding imports) to set up
Earthdata Login authentication, request and periodically refresh temporary S3
credentials, and serially transfer each granule. The equivalent `earthaccess` workflow
is about four lines (`login()`, `search_data()`, `open()`, and passing the result to
`xarray`) and additionally handles CMR-based discovery. Because that integration also
leverages `fsspec` for byte-range access, streaming a single variable across 28 granules
and computing a summary statistic completed in roughly 45 seconds end-to-end,
compared with roughly 78 seconds to download all 6.7 GB of those granules serially beforehand (medians
of three runs on the NASA-Openscapes `us-west-2` JupyterHub). Constructing or reading
virtual data stores over the same files with `VirtualiZarr` [@virtualizarr], which
enables reading only the requested chunks, can reduce access time further. The same
pattern applies to other products with large numbers of granules, such as ICESat-2 ATL06 land-ice height
data [@atl06], and is most pronounced where an analysis touches only a small portion of
each file.

**Contribute upstream.** When community discussions surface features
that belong in a dependency, the project contributes that work upstream rather than
absorbing it. Advanced CMR query capabilities were developed in `python-cmr` rather than
duplicated in `earthaccess`, and aspects of DMR++ parsing and multi-file virtual dataset
functionality were migrated to `VirtualiZarr` where they could benefit the wider
community. This upstream-first discipline prevents scope creep, reduces maintenance
burden, and strengthens the broader ecosystem that `earthaccess` depends on.

**Location-transparent access.** The same user code works whether the computation runs
in the cloud or on a local workstation, without requiring code changes; users who want
direct S3 access can request that optimization explicitly. This reflects the reality that researchers
are at varying stages of cloud adoption.

**Flat and functional top-level API.** All primary operations are exposed as module-level
functions (e.g., `earthaccess.login()`, `earthaccess.search_data()`,
`earthaccess.download()`), minimizing conceptual overhead for new users while keeping
the underlying object-oriented classes accessible for advanced use cases.


# Research impact statement

`earthaccess` has established itself as foundational infrastructure for NASA Earth
science data access. Concrete evidence of its impact includes:

**Peer-reviewed publications.** `earthaccess` has been used in published research,
including studies on multi-sensor drought observations in forested environments
[@andreadis2024] and tidal bore detection using SWOT satellite data [@arildsen2025].
Several other research studies and geospatial technology publications utilize libraries
dependent on `earthaccess`, including [@Scheick2025], [@Xiahou2026], [@Widlansky2025].

**Community adoption.** The library is a dependency of 260 public GitHub repositories
(as of 4 September 2026), spanning data analysis workflows, Jupyter Notebook tutorials, and
downstream libraries. It is distributed through both PyPI and conda-forge and 
installed and used in cloud-hosted Jupyter environments provided by NASA and partner
organizations. As one example of downstream adoption, `icepack` -- a finite element
library for ice sheet and glacier modeling [@shapero2021] -- replaced its hand-written
NSIDC DAAC data-fetching routines with `earthaccess` calls, eliminating hard-coded URLs
and custom authentication logic. Across NASA data access tutorials, `earthaccess` typically replaces tens of lines of setup code in each tutorial with a few function calls, increasing user accessibility and reducing the
overhead to "get started" working with NASA data.

**Multi-institutional development.** Contributors span NASA's Distributed Active Archive
Centers (DAACs) (including ASDC, ASF, GES DISC, LP DAAC, NSIDC DAAC, OB.DAAC, ORNL
DAAC, and PO.DAAC) as well as other federal and academic institutions (USGS, NOAA,
University of New Hampshire, University of Maryland, UC Berkeley), private industry (Coiled,
Development Seed), and independent open-source contributors. This breadth reflects both
the library's relevance across domains and the health of its contributor community.

**Integration with the NASA ecosystem.** `earthaccess` is featured in the official NASA
Earthdata tools catalog (<https://www.earthdata.nasa.gov/data/tools/earthaccess>) and in
NASA Earthdata tutorials. It has been presented at multiple large professional
meetings -- including several American Geophysical Union (AGU) Annual Meetings and Earth
System Information Partnership (ESIP) meetings -- and was the subject of a NASA ESDS
Tech Spotlight presentation (see <https://earthaccess.readthedocs.io> homepage for links
to recent slides and recordings). The documentation includes executable Jupyter
notebooks demonstrating workflows with ICESat-2, EMIT, TEMPO, SMAP, and other missions,
providing reproducible entry points for researchers.


# AI usage disclosure

The `earthaccess` project has adopted a contributor AI policy
(<https://earthaccess.readthedocs.io/en/latest/contributor/ai-policy/>) that requires
disclosure of AI assistance, holds contributors responsible for understanding and being
able to explain any code they submit, and prohibits fully autonomous AI-generated pull
requests. The version of `earthaccess` described here was developed without generative
AI assistance. Subsequent development may use AI tools under the terms of that policy.

Preparation of this manuscript was assisted by Claude [Sonnet 4.6, Opus 4.6, Opus 5, and Opus 5.5]
(Anthropic) using the repository source code,
documentation, commit history, and project metadata as context. Assistance was used for
manuscript drafting and editorial revision. All content was reviewed, revised, and
verified for accuracy by the authors, who bear full responsibility for the submitted
work.


# Acknowledgements

The development of `earthaccess` was supported by NASA's Earth Science Data Systems
(ESDS) program through the NASA Openscapes project (NASA award #20-TWSC20-2-0003
“Openscapes: Enabling a new era of science on the cloud, in response to the 2020 NASA
ROSES Element E2”, Julie Lowndes and Erin Robinson). We thank NASA Openscapes for the
community workshops, collaborative working environment, and people-first approach that
have motivated and continue to support this work. We are grateful to the National Snow
and Ice Data Center (NSIDC) for hosting the repository during its initial development
and to all contributors who have shaped `earthaccess` through contributing code,
documentation, issue reports, and community engagement. People 
contribute to earthaccess as adopters and developers as part of their jobs across the
NASA ecosystem as well as outside of it, which is critical to making this
shared resource successful. We appreciate everyone who advocates for and uses approved
time to make this possible. We also thank Allison Horst for the `earthaccess` artwork
and Daniel Kaufman for leading the preparation of this submission.


# References
