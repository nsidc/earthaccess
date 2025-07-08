# Contributing

Thank you for your interest in contributing to _earthaccess_! We're excited for your contribution,
whether you're finding bugs, adding new features, fixing anything broken, or improving documentation.

When contributing we recommend:

- reading the contributing guide all the way though once before starting
- [join us on Zulip chat](https://earthaccess.zulipchat.com) for any questions you may have
- searching through issues, discussions, pull requests, and Zulip to see if your contribution has already been discussed
  so you don't duplicate work

Then, you can:

- Open [a GitHub issue](https://github.com/nsidc/earthaccess/issues) to report a bug, unexpected behavior, a stumbling block in our documentation, or any
  other problem.
- Open [a Q&A GitHub Discussion](https://github.com/nsidc/earthaccess/discussions/categories/new?category=q-a) to ask
  questions, share insights, or connect with others about Earth data access (broadly)
- Open [an Ideas GitHub Discussion](https://github.com/nsidc/earthaccess/discussions/new?category=ideas) to suggest
  new features or improvements, and find collaborators and coordinate the work
- Join [a "hack day"](our-meet-ups.md) to meet other users/developers/maintainers and get help on, or give help to,
  anything related to Earth data access

You can also directly [open a pull request](#steps-to-a-pull-request) after you've reviewed this whole contributing guide.

If you're not sure what to do, _don't worry_, and just pick whichever suits you best. The community will help you out!

!!! note

    We have a [code of conduct](./code-of-conduct.md). Please follow it in all of your interactions with the project.

## Steps to a Pull Request

First, [fork this repository](https://github.com/nsidc/earthaccess/fork) and set up your [development environment](./development.md).

From here, you might want to fix and issue or bug, or add a new feature. Jump to the
relevant tab to proceed.

!!! tip

    The smaller the pull request, the easier it is to review and test, and the more likely it is to be successful. For more details, check out this [helpful YouTube video by the author of pre-commit](https://www.youtube.com/watch?v=Gu6XrmfwivI).

    For large contributions, consider opening  [an Ideas GitHub Discussion](https://github.com/nsidc/earthaccess/discussions/new?category=ideas)
    or [coming to a "hack day"](our-meet-ups.md) and describing your contribution so we can help guide and/or collaborate
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
    - Describe your changes in the `CHANGELOG.md`

Once you've completed these steps, you are ready to submit your pull request.

## Submitting your contribution

When you're ready to submit your pull request, first open a draft pull request and confirm that:

- You've included an explanation of what you did and why in the pull request
- All unit tests run successfully in your branch
- Your code is linted and formatted correctly
- The documentation and `CHANGELOG.md` has been updated appropriately

Then you can mark the pull request as ready for review! 🎉
