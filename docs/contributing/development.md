# Development

## Getting the code

1. [Fork nsidc/earthaccess](https://github.com/nsidc/earthaccess/fork)
1. Clone your fork:
   ```bash
   git clone git@github.com:{my-username}/earthaccess
   ```

In order to develop new features or fix bugs etc. we need to set up a virtual
environment and install the library locally.

## Quickstart development

The fastest way to start with development is to use nox. If you don't have nox,
you can use `pipx run nox` to run it without installing, or `pipx install nox`.
If you don't have pipx (pip for applications), then you can install with
`pip install pipx` (the only case were installing an application with regular
pip is reasonable). If you use macOS, then pipx and nox are both in brew, use
`brew install pipx nox`.

To use, run `nox` without any arguments.  This will run the type check and unit
test "sessions" (tasks) using your local (and active) Python version.
Nox handles everything for you, including setting up a temporary virtual
environment for each run.

You can see all available sessions with `nox --list`:

```
$ nox --list
Sessions defined in earthaccess/noxfile.py:

* typecheck -> Typecheck with mypy.
* tests -> Run the unit tests.
- test-min-deps -> Run the unit tests using the lowest compatible version of all direct dependencies.
- integration-tests -> Run the integration tests.
- build-pkg -> Build a source distribution and binary distribution (wheel).
- serve-docs -> Build the documentation and serve it.

sessions marked with * are selected, sessions marked with - are skipped.
```

You can also run individual tasks (_sessions_ in `nox` parlance, hence the `-s`
option below), like so:

```bash
nox -s integration-tests
```

and pass options to the underlying session like:

```bash
nox -s integration-tests -- [ARGS]
```

!!! tip

    In order to run integration tests locally, you must set the
    environment variables `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` to your
    username and password, respectively, of your
    [NASA Earthdata](https://urs.earthdata.nasa.gov/) account (registration is
    free).



## Manual development environment setup

While `nox` is the fastest way to get started, you will likely need a full
development environment for making code contributions, for example to test in a
REPL, or to resolve references in your favorite IDE.  This development
environment also includes `nox`. You can create it with `venv`, `conda`, or `mamba`.

=== "`venv`"

    `venv` is a virtual environment manager that's built into Python.

    Create and activate the development environment with:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

    Then install `earthaccess` into the environment in editable mode with the optional development dependencies:

    ```bash
    python -m pip install --editable ".[dev,test,docs]"
    ```


=== "`conda`/`mamba`"

    `conda` and `mamba` are open-source package and environment managers that are language and platform agnostic.
    `mamba` is a newer and faster re-implementation of `conda` -- you can use either `conda` or `mamba`
    in the commands below.

    Create and activate the development environment with:

    ```bash
    mamba env update -f environment.yml
    mamba activate earthaccess
    ```

    This will update (or create if missing) the `earthaccess` environment and active it. The `earthaccess` package will
    be installed into the environment in editable mode with the optional development dependencies.

## Managing Dependencies

If you need to add a new dependency, edit `pyproject.toml` and insert the
dependency in the correct location (either in the `dependencies` array or under
`[project.optional-dependencies]`).

## Usage of pre-commit

To maintain code quality, we use pre-commit for automated checks before committing changes. We recommend you install
and configure pre-commit so you can format and lint as you go instead of waiting for CI/CD check failures and
having to make significant changes to get the checks to pass.

To set up pre-commit, follow these steps:

- `python -m pip install pre-commit` ([official installation docs](https://pre-commit.com/#install))
- `pre-commit install` to enable it to run automatically for each commit
- `pre-commit run -a`  to run it manually

## Type stubs

We have included type stubs for the untyped `python-cmr` library, which we intend to eventually upstream.
Since `python-cmr` exposes the `cmr` package, the stubs appear under `stubs/cmr`.


## Documentation

To work on documentation locally, we provide a script that will automatically re-render the docs when you make changes:

```
nox -s serve_docs
```

MkDocs does not support incremental rebuilds and will execute every Jupyter Notebook every time it builds a new
version of the site, which can be quite slow. To speed up the build, you can pass MkDocs these options:

```
nox -s serve_docs -- --dirty --no-strict
```

!!! warning

    Our mkdocs setup has a known limitation: the hot reloader won't auto-reload when changing docstrings.
    To see updates, manually rebuild and re-serve docs. We're working to improve the developer experience and
    appreciate your patience.

### Documentation Style

To ensure that our code is well-documented and easy to understand, we use [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) to document
all functions, classes, and methods in this library.
