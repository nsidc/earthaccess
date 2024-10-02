<!--
Replace this text, including the symbols above and below it, with descriptive text about
the change you are proposing. Please include a reference to any issues addressed or
resolved in that text, for example "resolves #1".
-->

<!--
IMPORTANT: As a contributor, we would like as much help as you can offer, but we only
expect you to complete the steps in the "PR draft checklist" below. Maintainers are
willing and ready to help pick it up from there!

Please start by opening this Pull Request as a "draft". You can do this by
clicking the arrow on the right side of the green "Create pull request" button. While
your pull request is in "draft" state, maintainers will assume the PR isn't ready for
their attention unless they are specifically summoned using GitHub's @ system.

Follow the draft checklist below to move the PR out of draft state. If you accidentally
created the PR as a non-draft, don't worry, you can still change it to a draft using the
"Convert to draft" button on  the right side panel under the "Reviewers" section.
-->

<details><summary>Pull Request (PR) draft checklist - click to expand</summary>

- [ ] Please review our
      [contributing documentation](https://earthaccess.readthedocs.io/en/latest/contributing/)
      before getting started.
- [ ] Populate a descriptive title. For example, instead of "Updated README.md", use a
      title such as "Add testing details to the contributor section of the README".
      Example PRs: [#763](https://github.com/nsidc/earthaccess/pull/763)
- [ ] Populate the body of the pull request with:
    - A clear description of the change you are proposing.
    - Links to any issues resolved by this PR with text in the PR description, for
      example `closes #1`. See
      [GitHub docs - Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue).
- [ ] Update `CHANGELOG.md` with details about your change in a section titled
      `## Unreleased`. If such a section does not exist, please create one. Follow
      [Common Changelog](https://common-changelog.org/) for your additions.
      Example PRs: [#763](https://github.com/nsidc/earthaccess/pull/763)
- [ ] Update the documentation and/or the `README.md` with details of changes to the
      earthaccess interface, if any. Consider new environment variables, function names,
      decorators, etc.

Click the "Ready for review" button at the bottom of the "Conversation" tab in GitHub
once these requirements are fulfilled. Don't worry if you see any test failures in
GitHub at this point!

</details>

<details><summary>Pull Request (PR) merge checklist - click to expand</summary>

Please do your best to complete these requirements! If you need help with any of these
requirements, you can ping the `@nsidc/earthaccess-support` team in a comment and we
will help you out!

- [ ] Add unit tests for any new features.
- [ ] Apply formatting and linting autofixes. You can add a GitHub comment in this Pull
      Request containing "pre-commit.ci autofix" to automate this.
- [ ] Ensure all automated PR checks (seen at the bottom of the "conversation" tab) pass.
- [ ] Get at least one approving review.

</details>
