# Decision Record: [#231 AWS us-west-2 checking method](https://github.com/nsidc/earthaccess/issues/231)

- Status: Accepted  <!-- optional -->
- Deciders: @jhkennedy, @chuckwondo, @mfisher87, @Sherwin-14, @asteiker, @itcarroll
- Date: 2025-05-13
<!-- - Tags: [space and/or comma separated list of tags] optional -->

Technical Story: [#231 AWS us-west-2 checking method](https://github.com/nsidc/earthaccess/issues/231)

## Context and Problem Statement

Users have reported issues with our approach to determining "in-region" status (e.g. [#444](https://github.com/nsidc/earthaccess/issues/444)). Currently, `earthaccess` utilizes `earthaccess.__store__.in_region: bool` to check if the user is in the `us-west-2` AWS region, and uses that flag to control whether data is accessed "directly" in S3 or via HTTPS URLs routed through egress applications (e.g., [Cumulus](https://github.com/nasa/cumulus)) or [TEA](https://github.com/asfadmin/thin-egress-app)). However, this implementation has a number of issues:
- this is NASA centric (other agencies may use different regions, or clouds)
- this is not uniform w/in NASA (e.g., some data is in `us-east-1`)
- there is no reliable way to determine which region you are in, or if you are even in AWS

In general, users may want to know if they are working in the same region as the data so that they can:
- use `S3` aware tools that expect `S3://` URIs
- have more performant access^
- not "egress" data outside of Amazon, unless they explicitly want to^^

!!! note

    ^If the users is "in-region", HTTPS URLs will get redirected to signed S3 URLs by the egress application, so there is a small performance hit to using HTTPS URLs always, which will be more apparent when accessing a large number of objects like Zarr stores, where each object will have its own unique URL that will need to be redirected.

!!! note

    ^^There was some discussion on whether egressing data outside of AWS is a user concern, or not, outside of performance. Generally, NASA's policy is that it is *not* -- users can access the data freely, in any manner, at no direct cost, and it's NASA's responsibility to ensure the data is distributed in a cost-effective manner. However, some users do want to be good citizens and know if they are causing egress charges to be incurred, or to know if they are egressing data unexpectedly.

In terms of UX, the major question discussed in [#231](https://github.com/nsidc/earthaccess/issues/231) is whether to take a "look before you leap" (LBYL) approach by performing an up-front in-region check, or whether to take an "easier to ask forgiveness than permission" (EAFP) approach by handling an access error after it occurs.

For the LBYL approach:
- There's no technical way to do this that works across all AWS services (e.g., Fargate, EC2) or within infrastructure built inside AWS (e.g., a JupyterHub). So, earthaccess would likely have to use a set of "canary" files in each supported region and check (using an EAFP pattern under the hood) if those file were accessible directly.

For the EAFP approach, earthaccess would:
- Provide a way to specify what access mechanism you'd like (direct S3 or egress HTTPS), and if other methods should be fallen back on.
- Attempt to access the data using the user-preferred method and handle access errors by:
  - raising an error if no fallback method was selected
  - raising a warning and falling back to the alternate method


!!! info

    Both the LBYL approach and the EAFP approach will require development work to get working well, this decision is about which approach we prefer, so that development work can be directed well.


## Considered Options

1. (Outright rejected; no real consideration given) Don't provide any special handling and only support HTTPS access
2. Use a LBYL approach and attempt to determine the region before accessing data
3. Use an EAFP approach and by default, prefer direct S3 access and fall back to HTTPS
4. Use an EAFP approach and by default, prefer HTTPS access


!!! info

    for both (3) and (4), users will be able to specify which method they prefer and if they want to fall back to the other.

## Decision Outcome

Chosen option: "(4)", because:
* supporting direct access is critical to our community (outright rejecting (1))
* there is no technical way to do (2) without standing up permanent infrastructure earthaccess isn't funded to maintain
* and (4), as compared to (3), because it's simpler and doesn't clutter user workflows with warnings that may be irrelevant

with the understanding that users _will_ be able to explicitly specify what access mechanism they'd like (direct S3 or egress HTTPS), and if other methods should be fallen back on.


### [option 2]

- Good, because it provides users direct, up-front knowledge and is a commonly requested pattern from users
- Bad, because it's not technically feasible without direct infrastructure costs and complexity

### [option 3]

- Good, because it allows users to control the access methods
- Good, because it will always work by default
- Bad, because it's a more complicated access pattern and may primarily fall back for a large segment of our users, which is
- Bad, because it may generate un-desired warnings by default

### [option 4]

- Good, because it allows users to control the access methods
- Good, because it will always work by default
- Bad, because it may be less performant in the cloud by default
