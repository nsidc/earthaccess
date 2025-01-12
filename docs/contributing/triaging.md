# Triaging guide

With constant influx of new issues, it's essential to prioritize and categorize them efficiently to ensure that the most important problems are addressed promptly. This document outlines our approach to triaging issues on GitHub, including guidelines for labeling and resolving issues, as well as best practices for maintaining a well-organized and up-to-date issue tracker.

## Labeling Issues

When labeling an issue, choose the label(s) that best describes the issue. Using labels consistently and accurately ensures that issues are trackable and searchable.


### Issue Types

- **type: bug**: Use for issues that identify bugs causing incorrect or unexpected behavior.
- **type: duplicate**: ...
- **type: enhancement**: ...
- **type: will not do**: ...

- **dependencies**: Use this label for issues concerning dependencies.

- **documentation**: Use this label for issues related to documentation.

- **library**: Use this label for issues related to core libraries or preparations for future plugin impacts.


### Requests and Feedback

- **enhancement**: Use this label for requests for new features or improvements to existing functionalities.

- **feedback**:  Use this label for issues where feedback is requested from the team or our community.

- **help**: Use this label for issues where additional help or contributions are needed.


### Special Labels

- **automation**: Use this label for issues related to the CI/CD pipeline or automation

- **duplicate**: Use this label for issues that are duplicates of existing ones.

- **good first issue** : Use this label to highlight issues good for newcomers who want to contribute to Earthaccess.

- **hackathon**: Use this label for issues to be discussed during hackdays.

- **wontfix**: Use this label for issues that won’t be addressed or fixed.


## Linking Labels in GitHub Markdown

When referencing a label in a GitHub issue or discussion, it will be  useful to link to the label page to provide additional context and help other members to quickly understand the issue's category.

### Syntax

To link to a label in GitHub Markdown, use the following syntax:

```
[label name](https://github.com/username/repository/labels/label-name)
```

### Example

For example, to link to the "hackathon" label in the nsidc/earthaccess repository, you would use the following syntax:

```
[hackathon](https://github.com/nsidc/earthaccess/labels/hackathon)
```

!!! tip
    When linking to labels, it is a good practice to use the label name as the link text, as shown in the example above. This makes it clear to others what label is being referenced, and helps to avoid confusion.

## Close Issue as Not Planned

This section will cover the guidelines for when to use the "Close Issue as Not Planned" label, and how to handle issues that are not planned or feasible.

### When to Use This Label?

Close issues as "not planned" when:

- An issue is not aligned with the project's goals or priorities.
- An issue is not feasible to be addressed due to technical or resource constraints.
- An issue is a duplicate of an existing issue that has already been addressed.

When closing an issue as not planned, keep the following best practices in mind:

- Provide a clear explanation as to why the issue is not planned or feasible.
- Offer alternative solutions or workarounds, if possible.
- Link to relevant documentation or resources, if applicable.

## Discussions vs Issues

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

- The issue is a feature request or idea.
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
  start ==NO==> close1[Change
  to draft and ask to follow template]
  start == YES ==> dupe{Is duplicate?}
  dupe == YES ==> close2[Close and point to duplicate]
  dupe == NO ==> repro{Has proper reproduction?}
  repro == NO ==> close3[Label: 'needs reproduction' bot will auto close if no update has been made in 3 days]
  repro == YES ==> real{Is actually a bug?}
  real == NO ==> intended{Is the intended behaviour?}
  intended == YES ==> explain[Explain and close point to docs if needed]
  intended == NO ==> open[Keep open for discussion Remove 'pending triage' label]
  real == YES ==> real2["1. Remove 'pending triage' label 2. Add related feature label if applicable (e.g. 'feat: ssr') 3. Add priority and meta labels (see below)"]
  real2 ==> unusable{Does the bug make earthaccess unusable?}
  unusable == YES ==> maj{Does the bug affect the majority of earthaccess users?}
  maj == YES ==> p5[p5: urgent]
  maj == NO ==> p4[p4: important]
  unusable == NO ==> workarounds{Are there workarounds for the bug?}
  workarounds == NO ==> p3[p3: minor bug]
  workarounds == YES ==> p2[p2: edge case has workaround]

  %% Link Color %%
    linkStyle default stroke:black,stroke-width:2px,font-size:24pt;

```
