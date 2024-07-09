# Contributing

When contributing to this repository, please first discuss the change you wish to make
with the community and maintainers via
[a GitHub issue](https://github.com/nsidc/earthaccess/issues),
[a GitHub Discussion](https://github.com/nsidc/earthaccess/discussions),
or [any other method](our-meet-ups.md).

Please note that we have a [code of conduct](./code-of-conduct.md). Please follow it in all of your interactions with the project.

## First Steps to contribute

- Read the documentation!
- Fork this repo and set up development environment (see
  [development environment documentation](./development.md) for details)
- Run the unit tests successfully in `main` branch:
    - `make test`

From here, you might want to fix and issue or bug, or add a new feature.  Jump to the
relevant section to proceed.

### ...to fix an issue or bug

- Create a GitHub issue with a
  [minimal reproducible example](https://en.wikipedia.org/wiki/Minimal_reproducible_example),
  a.k.a Minimal Complete Verifiable Example (MCVE), Minimal Working Example (MWE),
  SSCCE (Short, Self Contained, Complete Example), or "reprex".
- Create a branch to resolve your issue
- Run the unit tests successfully in your branch
- Create one or more new tests to demonstrate the bug and observe them fail
- Update the relevant code to fix the issue
- Successfully run your new unit tests

Once you've completed these steps, you are ready to submit your contribution.

### ...to contribute a new feature

- Create an issue and discuss the feature's scope and its fit for this package with the team
- Create a branch for your new feature in your fork
- Run the unit tests successfully in your branch
- Write the code to implement your new feature in a backwards compatible manner
- Create at least one test that exercises your feature and run the test suite as you go

Once you've completed these steps, you are ready to submit your contribution.

## Submitting your contribution

- Run all unit tests successfully in your branch
- Lint and format your code.  See below.
- Update the documentation and CHANGELOG.md
- Submit the fix to the problem as a pull request
- Include an explanation of what you did and why in the pull request

### Please format and lint as you go

```bash
make format lint
```

We attempt to provide comprehensive type annotations within this repository.  If
you do not provide fully annotated functions or methods, the `lint` command will
fail.  Over time, we plan to increase type-checking strictness in order to
ensure more precise, beneficial type annotations.

We have included type stubs for the untyped `python-cmr` library, which we
intend to eventually upstream.  Since `python-cmr` exposes the `cmr` package,
the stubs appear under `stubs/cmr`.

## Pull Request process

Fork the repository using the "Fork" button on the [repository
homepage](https://github.com/nsidc/earthaccess), create a branch with your changes in the fork, then open
a draft pull request from your fork. Starting a pull request provides additional instructions and requirements, and
there is no harm in starting a draft pull request while still developing.
