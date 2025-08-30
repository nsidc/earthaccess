# Decision Record: [#929 Move or fork to independent organization](https://github.com/nsidc/earthaccess/issues/929)

- Status: Ready for Review  <!-- optional -->
- Deciders: @jhkennedy, @chuckwondo, @mfisher87, @Sherwin-14, @asteiker, @itcarroll
- Date: 2025-07-08
<!-- - Tags: [space and/or comma separated list of tags] optional -->

Technical Story: [#929 Move or fork to independent organization](https://github.com/nsidc/earthaccess/issues/929)

## Context and Problem Statement

`earthaccess` currently lives under the `nsidc` organization.

While the `earthaccess` community lives under the ownership of a private
organization, GitHub's design prevents us from administrating our project
independently.
For example, we require organization owner permission for certain actions, teams are managed at the organization level, and our project is mixed with a large number of other projects (making it less discoverable).

Moving the `earthaccess` repo to another GitHub organization will:

* Reduce friction to collaboration by allowing us to self-determine our
  community members' access and privileges.
* Improve discoverability by reducing the amount of irrelevant items
  when browsing for related projects.
* Enable bundling related repositories (e.g. the R earthdatalogin project, other
  dependency libraries) under the same org, for example to cross-document project.
* Preserve community's ability to make its own decisions independent of
  institutional structure and policy.

Overall: enhance collaboration, efficiency, and longevity
In order to strengthen the community engagement of earthaccess and lower participation barriers, moving to a

Bullets from presentation to ESDIS on 2/11/2025:
- Accelerate development via broader participation
- Lower the cost:value even further for ESDIS
- Promote NASA’s partners

* Co-location with other similar projects (including similar resources in other languages, e.g. R and Julia)
* Meeting users where they are
* Increase visibility, ability to promote, bring awareness to a broader community (e.g. Pangeo showcase)
* Meets NASA Open Source Science goals
* Leveraging NUMFocus sponsorship could allow for Google Summer of Code mentorship and other funding/effort contributions
* Promotes NASA’s partnerships with other community members based on shared goals, by actively recognizing the critical * contributions of those members.
* From some Googling:
* Flexibility
* Rapid innovation
* Improved security through rapid bug fixes
* Transparency and trust
* Cost efficiency
* Development driver by the user community
* While inter-community support reduces ESDIS/NASA required support, we acknowledge that increased ESDIS funding will also help us sustain the library
hips with other community members based on shared goals
- Increase sustainability



## Considered Options

?


## Decision Outcome

?


### Option 1

Don't move; stay within `nsidc` org.

### Option 2

Move to an independent org, e.g. `earthaccess-dev`.

### Option 3

Move to a sponsor / incubator org, e.g. `pangeo`.
