# Issue Triaging and Prioritization Guide

With a constant influx of new issues, it's essential to prioritize and categorize them efficiently to ensure that the most important problems are addressed promptly. This document outlines our approach to triaging issues on GitHub, including guidelines for labeling and resolving issues, as well as best practices for maintaining a well-organized, prioritized, and up-to-date issue tracker via the `earthaccess` [GitHub Project](https://github.com/orgs/earthaccess-dev/projects/1). 

!!! tip

    We hope that this guide will help empower anyone to contribute to issue triaging, and ultimately address a common question for both new and experienced contributors: "I'm interested in working on the highest priority issues that will solve important problems facing the `earthaccess` community. Where do I begin?"

## Issue Lifecycle

1. A [new issue](https://github.com/earthaccess-dev/earthaccess/issues/new/choose) is created, either using a pre-existing template, or as a blank issue.
2. The issue is triaged in order to: 
   * Determine whether the issue should be pursued and moved to a Backlog status, or closed as not planned.
   * Add or adjust issue labels.
   * Add an issue prioritization. 
   * Respond and follow up as needed (i.e. tagging relevant earthaccess maintainers for further support).
3. Issues are reviewed and groomed using the `earthaccess` [GitHub Project](https://github.com/orgs/earthaccess-dev/projects/1)
4. An issue is worked following the [Pull Request (PR) Guiide](./pr-guide.md).
   * The issue is self-assigned and moved to an `In Progress` status.
   * The issue is linked to the related PR, and closed after the PR is merged.

Details on each of these workflow steps are provided below. 

## Moving an issue to Backlog status

This section will cover the `earthaccess` project status, guidelines for when to use the "Close Issue as Not Planned" feature, and how to handle issues that are not planned or feasible.

### Project status

By default, all new issues are created without a project status. Issues without a status are listed in the [Needs Triage](https://github.com/orgs/earthaccess-dev/projects/1/views/3) project view. Statuses include:
- Backlog
- In Progress
- In Review
- Done

Move the issue to the Backlog unless it ought to be closed as "not planned", as outlined below. On the righthand side of the issue page, the "Projects" section contains an `earthaccess` project box. Click "no status" to select the status options. Select "Backlog". This will move the project out of the [Needs Triage](https://github.com/orgs/earthaccess-dev/projects/1/views/3) project view into its relevant backlog view depending on issue type. See below for more details on these other project views.

### Close Issue as Not Planned

#### When to "Close as not planned"?

Close issues as "not planned" when:

- An issue is not aligned with the project's goals or priorities.
- An issue is not feasible to be addressed due to technical or resource constraints.
- An issue is a duplicate of an existing issue that has already been addressed.

When closing an issue as not planned, keep the following best practices in mind:

- Provide a clear explanation as to why the issue is not planned or feasible.
- Offer alternative solutions or workarounds, if possible.
- Link to relevant documentation or resources, if applicable.
- Add the **type: will not do** label.


## Labeling Issues

When labeling an issue, choose the label(s) that best describes the issue. Using labels consistently and accurately ensures that issues are trackable and searchable.


### Issue Types

- **type: bug**: Use for issues that identify bugs causing incorrect or unexpected behavior. This label is applied automatically if the [Bug template](https://github.com/earthaccess-dev/earthaccess/issues/new?template=bug.yml) is used.
- **type: decision record**: Use this label for issues and PR's that address a new decision record document (e.g. https://github.com/earthaccess-dev/earthaccess/pull/1047).   
- **type: duplicate**: Use this label for issues that are duplicates of existing ones.
- **type: enhancement**: Use this label for requests for new features or improvements to existing functionalities.
- **type: experience report**: Use this label for issues that include the reporter's usability experience 
- **type: metrics**: This label is automatically applied upon creation of the Monthly metrics issue. See the [Monthly issue metrics](https://github.com/earthaccess-dev/earthaccess/blob/main/.github/workflows/issue-metrics.yml) action for more details.  
- **type: will not do**: Use this label for issues that won’t be addressed or fixed.

### Impact labels

These labels describe what portion of the project they affect:

- **impact: breaking**: Issues that break our public API.
- **impact: core**: Issues that affect the core Python codebase.
- **impact: dependencies**: Use this label for issues concerning dependencies.
- **impact: documentation**: Use this label for issues related to documentation.
- **impact: automation**: Use this label for issues related to the CI/CD pipeline or automation

### Needs labels

- **needs: decision**: We're struggling to decide what to do and the decision committee needs to help.
- **needs: feedback**:  Use this label for issues where feedback is requested from the team or our community.
- **needs: help**: Use this label for issues where additional help or contributions are needed.

### Special labels

- **good first issue**: Use this label for issues that are suitable for new contributors. These issues are designed to be approachable and not overly complex, making them an ideal starting point for those looking to contribute to the project.

## Linking Labels in GitHub Markdown

When referencing a label in a GitHub issue or discussion, it will be  useful to link to the label page to provide additional context and help other members to quickly understand the issue's category.

### Syntax

To link to a label in GitHub Markdown, copy-and-paste the URL to the label by right-clicking [any label](https://github.com/earthaccess-dev/earthaccess/labels) and selecting "Copy Link". Then, paste that label in a GitHub issue, PR, discussion, or Markdown document:

```
https://github.com/username/repository/labels/label-name
```

### Example

For example, to link to the "good first issue" label in the earthaccess-dev/earthaccess repository, you would use the URL:

```
https://github.com/earthaccess-dev/earthaccess/labels/good%20first%20issue
```

## Issue Prioritization

TODO

Definitions of priority labels for docs:
**Critical:**
- If it’s broken
- Would a user see this and immediately stop using the docs
**Important:**
- Does it impact primary user workflows but not necessarily broken
**Nice to have:** 
- Sprinkles and confetti 
- Contributoring docs lower priority than end-users
- Depends on doc sections:
-- User guide: main audience is the end user
https://earthaccess.readthedocs.io/en/latest/contributor/ vs https://earthaccess.readthedocs.io/en/latest/user/, https://earthaccess.readthedocs.io/en/latest/api/ (contributor is also the user), and Overview (https://earthaccess.readthedocs.io/en/latest/) 


## Discussions vs Issues
TODO Move to https://earthaccess.readthedocs.io/en/latest/contributor/ 

This section would cover the guidelines for when to use discussions versus issues, and how to migrate between them.

###  What are Discussions?

Discussions are used for:

- Brainstorming and idea generation.
- Project feedback.
- General questions and topics.

###  What are Issues?

Issues are used for:

- Reporting bugs and errors.
- Tracking progress on specific tasks or projects.
- Requesting changes or improvements.

### When to Migrate

Use your best judgement when migrating between issues and discussions. Sometimes it makes more sense to open a new issue or discussion instead of migrating, for example when there are many things being discussed, but we want to create an issue or task out of just one of those things.

Migrate a discussion to an issue when:

- A specific task is identified.
- A bug or error is reported.
- A change or improvement is requested.

Migrate an issue to a discussion when:

- The issue is a nebulous idea that needs to be workshopped before it can be implemented.
- The issue is a general question or topic.
- The issue is not specific or actionable.

## Issue Triaging Workflow

``` mermaid

flowchart TD
  %%{init: {"flowchart": {"htmlLabels": false}} }%%
  classDef default font-size:32pt;
  start{"`Followed
  issue
  template?`"}
  start ==NO==> close1[Request needed information from reporter and update issue on behalf of reporter]
  start == YES ==> dupe{Is duplicate?}
  dupe == YES ==> close2[Close and point to duplicate]
  dupe == NO ==> repro{Has proper reproduction?}
  repro == NO ==> close3[Label: 'needs reproduction' bot will auto close if no update has been made in 3 days]
  repro == YES ==> real{Is actually a bug?}
  real == NO ==> intended{Is the intended behaviour?}
  intended == YES ==> explain[Explain and close point to docs if needed]
  intended == NO ==> open[Keep open for discussion Remove 'pending triage' label]
  real == YES ==> real2["Confirm that 'Bug' label was automatically added as part of the Bug Issue template, otherwise add 'Bug' label."]


  %% Link Color %%
    linkStyle default stroke:black,stroke-width:2px,font-size:24pt;

```
