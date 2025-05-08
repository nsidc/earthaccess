# Maintainers Guide

This page offers guidance to project maintainers regarding our setup procedures, release processes, package creation, and other related tasks.

## Maintainer Onboarding and Best Practices

### Becoming a Maintainer or Triager

If you are interested in becoming a maintainer, you can join our community. Maintainers have several important responsibilities, so please read on to understand the role.

Also, if you're interested in helping manage issues with labels and interacting with incoming requests, you can have a "triager" role!

To get permissions, please start by participating on GitHub by answering questions, reviewing PRs, or contributing code or documentation. Once you're feeling comfortable, you can ask any of our maintainers for permissions by `@`ing them on GitHub.

### Maintainer Responsibilities and Expectations

1. As a maintainer, there is no strict time obligation, as we understand that everyone's ability to commit can fluctuate. However, we do expect maintainers to communicate openly and transparently with the team and the community.

2. As a maintainer, you are expected to uphold a positive team culture. This includes following the guidelines outlined in the [Openscapes team culture page](https://openscapes.github.io/series/core-lessons/team-culture.html) and the [recorded psychological safety talk](https://www.youtube.com/watch?v=rzi-qkl8u5M) . By doing so, you can help ensure that all team members and contributors feel safe, respected, and valued.


### Maintainer Processes Beyond Regular Contributing

1. As a maintainer, label issues clearly and consistently to help contributors identify issue types and priority. Use 'good first issue' for contributor-friendly issues.

2. As a maintainer, create welcoming environment when communicating with contributors (issue / PR / discussion posters).

3. As a maintainer reviewing and merging contributions is critical. Here are some best practices:

    3a. Review contributions thoroughly.

    3b. Provide constructive feedback.

    3c. Communicate clearly and respectfully.

    3d. Merge contributions promptly.

4. As a maintainer, you will be releasing different versions. More on this in [here](./releasing.md).

## Branches

main: This is the main branch, which is consistently tested and prepared for release as a new version. Avoid pushing changes directly to this branch. Instead, create a new branch and submit a pull request for any modifications.


## Continuous Integration & Delivery

The GitHub Actions CI services handle the project's building, testing, and management across Linux, macOS, and Windows platforms. The CI configuration files can be found in the `./.github/workflows/`.


## Continuous Documentation

[ReadTheDocs](https://readthedocs.org/projects/earthaccess/) is used to generate and host [our documentation website](https://earthaccess.readthedocs.io/) as well as the preview for documentation changes made in pull requests. This service uses a configuration file in the root of the project, `.readthedocs.yml`.
