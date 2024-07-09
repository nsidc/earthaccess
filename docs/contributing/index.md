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

### Fixing an Issue or Bug

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

### Contributing a New Feature

- Create an issue and discuss the feature's scope and its fit for this package with the team
- Create a branch for your new feature in your fork
- Run the unit tests successfully in your branch
- Write the code to implement your new feature in a backwards compatible manner
- Create at least one test that exercises your feature and run the test suite as you go

Once you've completed these steps, you are ready to submit your contribution.


### Contributing to Documentation

#### Documentation Style

To ensure that our code is well-documented and easy to understand, we use [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) to document all functions, classes, and methods in this library.

#### Locally rendering the documentation

To work on documentation locally, we provide a script that will automatically re-render the docs when you make changes:

```
./scripts/docs-live.sh
```

If you encounter any issues while setting up the documentation using the provided steps, please refer to our [tutorial]( https://www.youtube.com/watch?v=mNjlMZ4F3So) for additional guidance.

##### Caveats and considerations

Our mkdocs setup has a known limitation: the hot reloader won't auto-reload when changing docstrings. To see updates, manually rebuild and re-serve docs. We're working to improve the developer experience and appreciate your patience.


## Submitting your contribution

- Run all unit tests successfully in your branch
- Lint and format your code.  See below.
- Update the documentation and CHANGELOG.md
- Submit the fix to the problem as a pull request
- Include an explanation of what you did and why in the pull request

### Please format and lint as you go


#### Usage of Pre-Commit

To maintain code quality, we use pre-commit for automated checks before committing changes. Install and configure pre-commit to ensure high-quality contributions.

To set up pre-commit, follow these steps:

- `pip install pre-commit` ([official installation docs](https://pre-commit.com/#install))
- `pre-commit install` to enable it to run automatically
- `pre-commit run -a`  to run it manually


We have included type stubs for the untyped `python-cmr` library, which we intend to eventually upstream.  Since `python-cmr` exposes the `cmr` package, the stubs appear under `stubs/cmr`.

## Pull Request process

Fork the repository using the "Fork" button on the [repository
homepage](https://github.com/nsidc/earthaccess), create a branch with your changes in the fork, then open
a draft pull request from your fork. Starting a pull request provides additional instructions and requirements, and
there is no harm in starting a draft pull request while still developing.
