# Decision Record: [#929 Move or fork to independent organization](https://github.com/nsidc/earthaccess/issues/929)

- Status: Ready for Review  <!-- optional -->
- Deciders: @jhkennedy, @chuckwondo, @mfisher87, @Sherwin-14, @asteiker, @itcarroll, @danielfromearth
- Date: 2025-07-08
<!-- - Tags: [space and/or comma separated list of tags] optional -->

Technical Story: [#929 Move or fork to independent organization](https://github.com/nsidc/earthaccess/issues/929)

## Context and Problem Statement

`earthaccess` currently lives under the `nsidc` organization.

While the `earthaccess` community lives under the ownership of a private
organization, GitHub's design prevents us from administrating our project
independently.
For example, we require organization owner permission for certain actions, teams are managed at the organization level, and our project is mixed with a large number of other projects (making it less discoverable).

In order to strengthen the community engagement of earthaccess and lower participation barriers, moving the `earthaccess` repo to another GitHub organization will:

* Reduce friction to collaboration by allowing us to self-determine our
  community members' access and privileges.
* Improve discoverability by reducing the amount of irrelevant items
  when browsing for related projects.
* Enable bundling related repositories (e.g. the R earthdatalogin project, other
  dependency libraries) under the same org, for example to cross-document project.
* Preserve community's ability to make its own decisions independent of
  institutional structure and policy.

### Historical Context

A presentation by several earthaccess maintainers to NASA ESDIS on 2/11/2025 provided additional context and benefits of "repotting" the earthaccess repository, in order to learn more about their stance on moving and how this might impact future funding opportunities. This presentation highlighted other key benefits of repotting the repository, including: 

* Accelerating development via broader participation
* Lower the cost:value even further for NASA ESDIS by enabling rapid innovation and improved security through rapid bug fixes
* Promote NASA’s partnerships with other community members based on shared goals, by actively recognizing the critical contributions of those members and increasing transparency and trust.
* Meet NASA Open Source Science goals

An outcome of this meeting was to pursue a cross-DAAC proposal for sustained ESDIS funding, retaining the existing community ownership model while enhancing and amplifying the communication of feature development across the earthaccess community and ESDIS. While inter-community support reduces ESDIS/NASA required support, we acknowledge that increased ESDIS funding will also help us sustain the library. Although a draft was developed, ESDIS asked for this effort to be paused in summer 2025. Regardless of the approach we choose, we will continue acknowledging ESDIS support through our ESDIS-funded contributors and the facilitation role of NASA Openscapes. 

While earthaccess is listed by ESDIS as an approved Enterprise Solution, earthaccess is not part of ESDIS convergence...


### Migration effort tasks

Options 2 and 3 below would involve the movement of the existing earthaccess repository into another GitHub organization.

Transferring a GitHub repository to another organization involves several impacts and considerations:
1. Repository URL and Local Clones:
The repository's URL will change to reflect the new organization.
GitHub provides redirects from the old URL, but it is recommended to update local clones to point to the new URL using git remote set-url origin NEW-URL to avoid potential issues and confusion.
2. Permissions and Access:
Permissions and access settings will need to be reconfigured within the new organization.
Team members who previously had access may need to be granted access to the repository within the new organization's structure.
3. Integrations and Third-Party Tools:
Any integrations or third-party tools connected to the repository (e.g., CI/CD pipelines, project management tools) may be affected.
These tools will likely need to be updated or reconfigured to work with the repository's new location and potentially different access tokens or settings.
4. Issues, Pull Requests, and Project Details:
All existing issues, pull requests, and other project details (e.g., commit history, branches) will be transferred with the repository and remain intact.
However, if you are using classic GitHub Projects tied to the repository, they will not transfer and references to issues/PRs within them may break. New GitHub Projects (beta) issues will remain but may need manual re-association. 
5. GitHub Pages:
Links to the Git repository on the web and through Git activity will be redirected if the repository contains a GitHub Pages site.
However, the GitHub Pages site itself is not automatically redirected and may need manual adjustment or recreation in the new organization's context.
6. Forks:
If the repository was forked from a private upstream network, it cannot be transferred.
If the target organization already has a fork of the repository, the transfer cannot proceed.
7. Packages:
Packages associated with the repository may or may not transfer or retain their link, depending on the registry they belong to. Permissions for GitHub Packages should be reviewed. 
8. Notifications:
Users who previously interacted with the repository will receive a notification that the repository has been moved.

What are the things that don't need to be migrated

Issues, PRs, etc.

## Considered Options

### Option 1: Don't move; stay within `nsidc` org.

Pros:
* No migration effort (and associated disruption) needed

Cons:
* No clear path to extend organizational ownership permissions to earthaccess maintainers outside of NSIDC

### Option 2: Move to an independent org, e.g. `earthaccess-dev`.

Pros:
* Full / flexible community governance
* Custom branding?

Cons:
* Migration effort
* Potential for reduced visibility without institutional org backing?


### Option 3: Move to a sponsor / incubator org, e.g. `pangeo`, `openscapes`.

Pros:
* Built-in open source credibility and visibility
* Leverage existing communities, increased contributor base?
* Leverage existing software infrastructure?,
* Leverage existing governance models?
* Potential funding opportunities?
Cons:
* Migration effort
* Less control over organizationl decisions/policies/memership?
* May need to align with existing organization's priorities and processes



## Decision Outcome

?



