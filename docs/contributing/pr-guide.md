# Pull request guide

🤩 Our community is so excited to collaborate with you!

However, our maintainers are mostly volunteers.
In order to make the best use of their limited time, we ask that you follow this guide
when opening a PR.

When you open a PR, the description field will be auto-populated with some reminders and
checklists to that effect.
Please read them carefully!


## Checklist

### Start with a draft

Instead of clicking "Create pull request", please click the dropdown arrow to the right
of that button and select "Create draft pull request".

If you forget this step, you can "convert to draft" towards the top of the right side
panel.


### Review [contributing documentation](/contributing/index.md)

If you're new to our community, please ensure you're aware of how we organize
contributions.


### Be descriptive

* **Title**: For example, instead of `Updated README.md`, use `Add testing details to the
  contributor section of the README`.
  Example: [#763](https://github.com/nsidc/earthaccess/pull/763)
* **Body**:
    * Populate a clear description of the change you're proposing. What did you do, and
      **why**?
    * Link to any issues that describe the problem being solved.
    * Links to any issues resolved by this PR with text in the PR description, for example
      `closes #1`.
      See more in [GitHub docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue).


### Update documentation

* **`CHANGELOG.md`**: If you change the software (docs changes don't need a changelog
  entry), add details about your change in a section titled `## Unreleased`.
  If such a section does not exist, please create one at the top of the file.
  Follow [Common Changelog](https://common-changelog.org/) for your additions.
  Example: [#763](https://github.com/nsidc/earthaccess/pull/763)
* **`README.md`**: Update as needed, for example if installation or usage instructions
  need to change.


### Mark "Ready for review!"

Once you select "Ready for review", maintainers will give your PR their attention and
help complete any remaining steps if needed!

If you're not getting the help you need, please mention `@nsidc/earthaccess-support` in
a comment in your PR.


## Detailed guide

First, [fork this repository](https://github.com/nsidc/earthaccess/fork) and set up your [development environment](./development.md).

From here, you might want to fix and issue or bug, or add a new feature. Jump to the
relevant tab to proceed.

!!! tip

    The smaller the pull request, the easier it is to review and test, and the more likely it is to be successful. For more details, check out this [helpful YouTube video by the author of pre-commit](https://www.youtube.com/watch?v=Gu6XrmfwivI).

    For large contributions, consider opening  [an Ideas GitHub Discussion](https://github.com/nsidc/earthaccess/discussions/new?category=ideas)
    or coming to [a Collaboration Café](calendar.md) and describing your contribution so we can help guide and/or collaborate
    on the work.

=== "Fixing an Issue or Bug"

    - Create a [minimal reproducible example](https://en.wikipedia.org/wiki/Minimal_reproducible_example), a.k.a. a Minimal Complete Verifiable Example (MCVE),
      a Minimal Working Example (MWE), an SSCCE (Short, Self Contained, Complete Example), or a "reprex",
      and include it in [a GitHub issue](https://github.com/nsidc/earthaccess/issues) (recommended) or in your pull request.
    - Create a branch to resolve your issue
    - Run the existing unit tests successfully in your branch
    - Create one or more new tests to demonstrate the bug and observe them fail
    - Update the relevant code to fix the issue
    - Successfully run your new unit tests
    - Lint and format your code with [pre-commit](development.md#usage-of-pre-commit)
    - Describe your changes in the `CHANGELOG.md`

=== "Contributing a New Feature"

    - We recommend you create [an Ideas GitHub Discussion](https://github.com/nsidc/earthaccess/discussions/new?category=ideas)
      describing the feature's scope and its fit for this package with the team.
    - Create a branch for your new feature in your fork
    - Run the unit tests successfully in your branch
    - Write the code to implement your new feature in a backwards compatible manner. If breaking changes are necessary, discuss your strategy with the team first.
    - Create at least one test that exercises your feature and run the test suite
    - Lint and format your code with [pre-commit](development.md#usage-of-pre-commit)
    - Describe your changes in the `CHANGELOG.md`

=== "Contributing to Documentation"

    - Create a branch for your documentation changes in your fork
    - Update the documentation [following our style guide](development.md#documentation)
    - Preview the documentation [by rendering it locally](development.md#documentation). If you're not comfortable with this step, we'd rather you skip it and open a PR anyway! Our GitHub automations will generate a documentation preview. Please mark your PR as a draft until you've checked the preview and it looks OK. Don't hesitate to reach out for help!

Once you've completed these steps, you are ready to submit your pull request.
