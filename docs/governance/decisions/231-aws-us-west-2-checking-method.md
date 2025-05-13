# Decision Record: [#231 AWS us-west-2 checking method](https://github.com/nsidc/earthaccess/issues/231)

- Status: draft  <!-- optional -->
- Deciders: @jhkennedy, @chuckwondo, @mfisher87, @Sherwin-14, @asteiker, @itcarroll
- Date: 2025-05-13
<!-- - Tags: [space and/or comma separated list of tags] optional -->

Technical Story: [#231 AWS us-west-2 checking method](https://github.com/nsidc/earthaccess/issues/231)

## Context and Problem Statement

There is a user-desire to know if they are working in the same region as the data, which is typically in `us-west-2` for NASA data (but not always), so that they can use `S3` aware tools and/or have more performant in-place access. However, there is no reliable way to do this in AWS. So, there's a question of how we should handle `S3` access on the UX side, and how we handle that technically. 


## Decision Drivers <!-- optional -->

- Earthaccess thus far has used `earthaccess.__store__.in_region: bool` to check if the user is in `us-west-2`, but this is NASA centric and not even uniform w/in NASA.
- [driver 2, e.g., a force, facing concern, …]
- … <!-- numbers of drivers can vary -->

## Considered Options

1. Attempt to determine the region -- this is effectively a non-starter technically.
2. Defult to S3 access and fall back to HTTPS
3. Defult to HTTPS access and fall back to S3
4. Allow users to select (2) or (3) and HTTP/S3 only


## Decision Outcome

Chosen option: "[option 1]", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].

### Positive Consequences <!-- optional -->

- [e.g., improvement of quality attribute satisfaction, follow-up decisions required, …]
- …

### Negative Consequences <!-- optional -->

- [e.g., compromising quality attribute, follow-up decisions required, …]
- …

## Pros and Cons of the Options <!-- optional -->

### [option 1]

[example | description | pointer to more information | …] <!-- optional -->

- Good, because [argument a]
- Good, because [argument b]
- Bad, because [argument c]
- … <!-- numbers of pros and cons can vary -->

### [option 2]

[example | description | pointer to more information | …] <!-- optional -->

- Good, because [argument a]
- Good, because [argument b]
- Bad, because [argument c]
- … <!-- numbers of pros and cons can vary -->

### [option 3]

[example | description | pointer to more information | …] <!-- optional -->

- Good, because [argument a]
- Good, because [argument b]
- Bad, because [argument c]
- … <!-- numbers of pros and cons can vary -->

## Links <!-- optional -->

- [Link type][link to adr] <!-- example: Refined by [xxx](yyyymmdd-xxx.md) -->
- … <!-- numbers of links can vary -->