# Decision Record: [#929 Move or fork to independent organization](https://github.com/nsidc/earthaccess/issues/929)

- Status: Ready for Review  <!-- optional -->
- Deciders: @jhkennedy, @chuckwondo, @mfisher87, @Sherwin-14, @asteiker, @itcarroll, @danielfromearth, @JessicaS11
- Last updated: 2025-09-30
<!-- - Tags: [space and/or comma separated list of tags] optional -->

Technical Story: [#929 Move or fork to independent organization](https://github.com/nsidc/earthaccess/issues/929)

## Context and Problem Statement

`earthaccess` currently lives under the `nsidc` organization.

While the `earthaccess` community lives under the ownership of a private
organization, GitHub's design prevents us from administrating our project
independently.
For example, we require organization owner permission for certain actions, teams are managed at the organization level, and our project is mixed with a large number of other projects (making it less discoverable).

In order to strengthen the community engagement of earthaccess and lower participation barriers, moving the `earthaccess` repo to another GitHub organization will:

* Reduce friction to collaboration by allowing the community to self-determine its
  members' access and privileges.
* Improve discoverability by reducing the amount of irrelevant items
  when browsing for related projects.
* Enable bundling related repositories (e.g. the R earthdatalogin project, other
  dependency libraries) under the same org, for example to cross-document project.
* Preserve community's ability to make decisions based on the interests and needs of users,
  independent of institutional structure and policy.

### Historical Context

A presentation by several earthaccess maintainers to NASA ESDIS on 11 February 2025 provided additional context and benefits of "repotting" the earthaccess repository, in order to learn more about their stance on moving and how this might impact future funding opportunities. This presentation highlighted other key benefits of repotting the repository, including:

* Accelerating development via broader participation.
* Lowering the cost:value even further for NASA ESDIS by enabling rapid innovation and improved security through rapid bug fixes.
* Promoting NASA’s partnerships with other community members based on shared goals, by actively recognizing the critical contributions of those members and increasing transparency and trust.
* Meeting NASA Open Source Science goals.

Subsequent discussion included positive feedback from ESDIS on the value of earthaccess, and the desire to not disrupt the existing community development and engagement. An outcome of this meeting was to pursue a cross-DAAC proposal for sustained ESDIS funding, retaining the existing community ownership model while enhancing the communication of feature development across the earthaccess community and ESDIS. While inter-community support reduces ESDIS/NASA required support, we acknowledged in the proposal that increased ESDIS funding will also help us sustain the library. Although a proposal draft was developed, ESDIS asked for this effort to be paused in summer 2025. earthaccess is currently listed by ESDIS as an approved, operational Enterprise Solution, and was considered out of scope in broader tool and service convergence activities across other enterprise components. Regardless of the repository migration approach we choose, we will continue acknowledging ESDIS support through our ESDIS-funded contributors and the valuable facilitation role of NASA Openscapes.

### Migration effort tasks

Options 2 and 3 below would involve the movement of the existing earthaccess repository into another GitHub organization.

This transfer would be transparent to the earthaccess community in the following ways:

1. Repository URL (https://github.com/nsidc/earthaccess):
   * While the repository's URL will change to reflect the new organization, GitHub provides redirects from the old URL. Users who bookmark the old URL should not be negatively impacted.
2. Readthedocs URL (https://earthaccess.readthedocs.io/en/stable/):
   * This URL will not change even if the repository is migrated to a new GitHub organization.
3. Issues, Pull Requests, and Discussions:
   * All existing issues, pull requests, and other project details (e.g., commit history, branches) will be transferred with the repository and remain intact.
4. Forks:
   * According to GitHub [Transferring a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository#whats-transferred-with-a-repository) documentation, "If the transferred repository has any forks, then those forks will remain associated with the repository after the transfer is complete."
5. PyPI and conda-forge releases:
   * earthaccess publication to both PyPI and conda-forge package managers will continue as expected without any breaking changes.

This transfer would lead to the following administrative changes:

1. Local Clones:
   * According to GitHub [Transferring a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository#whats-transferred-with-a-repository) documentation, "All links to the previous repository location are automatically redirected to the new location. When you use git clone, git fetch, or git push on a transferred repository, these commands will redirect to the new repository location or URL. However, to avoid confusion, we strongly recommend updating any existing local clones to point to the new repository URL. You can do this by using git remote on the command line: `git remote set-url origin NEW_URL`
   * We will create an "explanation" page in our docs as a historical record and include instructions for updating local clones.
3. Permissions and Access to the new organization:
   * earthaccess maintainers would need to update permissions and access settings for team members within the new organization, as people who have access solely via NSIDC organization teams would lose access.
   * We may need to consider updates to our existing contributor documentation to reflect any applicable changes to our access processes.
3. Integrations and Third-Party Tools:
   * This may not apply to earthaccess, but we ought to consider whether any existing integrations in the NSIDC GitHub organization apply and would need to be re-connected to the migrated repository.
4. GitHub Project configuration
   * Classic GitHub Projects tied to the repository will not transfer and references to issues/PRs within them may break. We need to identify whether we are utilizing classic vs new (beta) projects. For the latter option, project configuration may remain but may need manual re-association.


## Considered Options

### Option 1: Don't move; stay within `nsidc` org.

Pros:
* No migration effort (and associated disruption) needed

Cons:
* Maintains sources of collaboration friction, such as there being no clear path to extend organizational ownership permissions to earthaccess maintainers outside of NSIDC
* Vulnerability to disruption by changes within the federal government, including shutdowns, funding changes, or dissolution of organizations.
* This project, and particularly, related repositories are hard to discover within the NSIDC GitHub org or aren't able to be placed within this org.
* Cross-repository actions and workflows are harder to orchestrate so documenting multiple related projects together (e.g., python_cmr, R earthdatalogin) is challenging

### Option 2: Move to an independent org, e.g. `earthaccess-dev`.

Pros:
* Overall benefits described above
* Full / flexible community governance
* Custom branding?

Cons:
* Migration effort
* Potential for reduced visibility without institutional org backing?


### Option 3: Move to a sponsor / incubator org, e.g. `pangeo`, `openscapes`.

Pros:
* Overall benefits described above
* Built-in open source credibility and visibility
* Leverage existing communities, increased contributor base?
* Leverage existing software infrastructure?,
* Leverage existing governance models?
* Potential funding opportunities?

Cons:
* Migration effort
* Less control over organizational decisions/policies/membership?
* May need to align with existing organization's priorities and processes


## Decision Outcome

TBD
