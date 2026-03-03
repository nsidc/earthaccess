---
title: 'earthaccess: A Python Library to Search for, and Download or Stream NASA Earth Science Data with Just a Few Lines of Code.'
tags:
  - Python
  - Earth science
  - data access
authors:
  - given-names: "Andrew"
    surname: "Barrett"
    orcid: "https://orcid.org/0000-0003-4394-5445"
    website: "https://github.com/andypbarrett"
    affiliation: "1, 2, 3"  # (Multiple affiliations must be quoted)
  - given-names: "Chris"
    surname: "Battisto"
    orcid: "https://orcid.org/0000-0002-9608-3634"
    website: "https://github.com/battistowx"
    affiliation: "1, 2, 3"
  - given-names: "James"
    surname: "Bourbeau"
    orcid: "https://orcid.org/0000-0003-2164-7789"
    website: "https://github.com/jrbourbeau"
    affiliation: "1, 2, 3"
  - given-names: "Matt"
    surname: "Fisher"
    orcid: "https://orcid.org/0000-0003-3260-5445"
    website: "https://mfisher87.github.io/"
    affiliation: "1, 2, 3"
  - given-names: "Daniel"
    surname: "Kaufman"
    orcid: "https://orcid.org/0000-0002-1487-7298"
    website: "https://github.com/danielfromearth"
    affiliation: "1, 2, 3"
  - given-names: "Joseph"
    surname: "Kennedy"
    orcid: "https://orcid.org/0000-0002-9348-693X"
    website: "https://github.com/jhkennedy"
    affiliation: "1, 2, 3"
  - given-names: "Luis"
    surname: "Lopez"
    orcid: "https://orcid.org/0000-0003-4896-3263"
    website: "https://github.com/betolink"
    affiliation: "1, 2, 3"
  - given-names: "Julia"
    surname: "Lowndes"
    orcid: "https://orcid.org/0000-0003-1682-3872"
    website: "https://github.com/jules32"
    affiliation: "1, 2, 3"
  - given-names: "Jessica"
    surname: "Scheick"
    orcid: "https://orcid.org/0000-0002-3421-4459"
    website: "https://github.com/JessicaS11"
    affiliation: "1, 2, 3"
  - given-names: "Amy"
    surname: "Steiker"
    orcid: "https://orcid.org/0000-0002-3039-0260"
    website: "https://github.com/asteiker"
    affiliation: "1, 2, 3"
  - given-names: "Sherwin"
    surname: "Varghese"
    orcid: "https://orcid.org/0009-0005-7030-213X"
    website: "https://github.com/Sherwin-14"
    affiliation: "1, 2, 3"
affiliations:
 - name: Place 1
   index: 1
 - name: Place 2
   index: 2
 - name: Place 3
   index: 3
date: 02 March 2026
bibliography: paper.bib
---

# Summary

<!--- A summary describing the high-level functionality and purpose of the software for a diverse,
non-specialist audience. --->

`earthaccess` revolutionizes NASA data access by drastically reducing the complexity and code
required. Since open science is a collaborative effort involving people from different technical
backgrounds, our team took the approach that data analysis can and should be made more inclusive
and accessible by reducing the complexities of underlying systems.


# Statement of need

<!--- A section that clearly illustrates the research purpose of the software and places it in the context of related work. This should clearly state what problems the software is designed to solve, who the target audience is, and its relation to other work. --->

It was hard as heck to get data before `earthaccess.`


# State of the field

<!--- A description of how this software compares to other commonly-used packages in the research area. If related tools exist, provide a clear “build vs. contribute” justification explaining your unique scholarly contribution and why existing alternatives are insufficient. --->

`earthaccess` builds and improves upon existing NASA metadata-related tools. In particular,
earthaccess leverages the querying capabilities of `Python-CMR` [@python_cmr], to interact with
 NASA's Earth science Common Metadata Repository (CMR).


# Software design

<!--- An explanation of the trade-offs you weighed, the design/architecture you chose, and why it matters for your research application. This should demonstrate meaningful design thinking beyond a superficial code structure description. --->

`earthaccess` is developed as an open-source package on GitHub; contributions
and feature suggestions are welcome. Continuous Integration using GitHub Actions ensures code
linting, formatting, version updating, and testing is routinely performed.
`earthaccess` is available on PyPI (The Python Package Index) via `pip`, `conda-forge` ().
It is released under the MIT license, and its source code is
available at https://github.com/earthaccess-dev/earthaccess.


# Research impact statement

<!--- Evidence of realized impact (publications, external use, integrations) or credible near-term significance (benchmarks, reproducible materials, community-readiness signals). The evidence should be compelling and specific, not aspirational. --->

`earthaccess` is used wherever someone needs an elegant and modern way to access NASA's Earth science data.


# AI usage disclosure

<!--- Transparent disclosure of any use of generative AI in the software creation, documentation, or paper authoring. If no AI tools were used, state this explicitly. If AI tools were used, describe how they were used and how the quality and correctness of AI-generated content was verified. --->

No generative AI tools were used in the development of this software, the writing
of this manuscript, or the preparation of supporting materials.


# Acknowledgements

<!--- Acknowledgement of any financial support. --->

This project was supported as part of Openscapes.


# References
