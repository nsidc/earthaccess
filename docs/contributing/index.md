# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the maintainers before making a change.

Please note that we have a [code of conduct](/CODE_OF_CONDUCT.md). Please follow it in all of your interactions with the project.

## First Steps to contribute

- Read the documentation!
- Fork this repo and set up development environment (see
  [development environment documentation](./development.md) for details)
- Run the unit tests successfully in `main` branch:
    - `make test`

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

### ...to contribute a new feature

- Create an issue and discuss the feature's scope and its fit for this package with the team
- Create a branch for your new feature in your fork
- Run the unit tests successfully in your branch
- Write the code to implement your new feature in a backwards compatible manner
- Create at least one test that exercises your feature and run the test suite as you go

## Submitting your contribution

- Run all unit tests successfully in your branch
- Lint and format your code
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

### Requirements to merge code (Pull Request Process)

- you must include test coverage
- you must update the documentation
- you must run the command above to format and lint

## Pull Request process

1. Ensure you include test coverage for all changes
1. Ensure your code is formatted properly following this document
1. Update the documentation and the `README.md` with details of changes to the
   interface, this includes new environment variables, function names,
   decorators, etc.
1. Update `CHANGELOG.md` with details about your change in a section titled
   `Unreleased`. If one does not exist, please create one.
1. You may merge the Pull Request once you have the sign-off of another
   developer, or if you do not have permission to do that, you may request the
   reviewer to merge it for you.
