# Development

## Getting the code

1. [Fork nsidc/earthaccess](https://github.com/nsidc/earthaccess/fork)
1. Clone your fork:
   ```bash
   git clone git@github.com:{my-username}/earthaccess
   ```
1. We recommend creating a feature branch when developing new features, fixing bugs, updating docs, etc. It's best to give the branch
a descriptive name For example, if you're updating the contributing docs, you might create a branch called `update-contributing-docs`:
   ```bash
   git switch -c update-contributing-docs
   ```

Next, In order to develop new features or fix bugs etc., you'll need to set up a virtual
environment and install the library locally.

## Development environment setup


There are a few options for setting up a development environment; you can use Python's `venv`, use `conda`/`mamba`, or _not_
manage one yourself and use `pipx` to run tests and build docs with `nox`.

* If you're a Windows user, you'll likely want to set up an environment yourself with `conda`/`mamba`.
* If you're working in a JupyterHub, you'll likely want to set up an environment yourself with `conda`/`mamba`.
* If you're using an IDE like VS Code or PyCharm, you'll likely want to set up an environment yourself with `venv` or `conda`/`mamba`.
* If you're using a plain text editor and don't know how to or want to manage a virtual environment, you'll likely want to start with `pipx`.

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

    After you have followed [the `conda`/`mamba` installation instructions](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) (we recommend Miniforge), you can create and activate the development environment with:

    ```bash
    mamba env update -f environment.yml
    mamba activate earthaccess
    ```

    This will ensure the `earthaccess` environment exists and is up-to-date, and active it. The `earthaccess` package will
    be installed into the environment in editable mode with the optional development dependencies.

    ??? note "2024-09-23: Conda environment name changed from `earthaccess-dev` -> `earthaccess`"

        On Sept. 23, 2024, the name of the conda environment changed from `earthaccess-dev` to `earthacess` to align with
        community best practices. If you have an `earthaccess-dev` environment, we recommend deleting it and creating a new one.
        From the repository root, you can do that with these commands:

        ```bash
        mamba env update -f environment.yml
        mamba activate earthaccess
        mamba env remove -n earthaccess-dev
        ```

=== "`pipx`+`nox`"

    `pipx` is a tool to help you install and run end-user applications written in Python and `nox` is Python application
    that automates testing in multiple Python environments. By using `pipx` to install `nox` and using `nox` to run common development tasks, some users can avoid the need to set up and manage a full development environment.
    Once you have [installed `pipx` following the official instructions](https://github.com/pypa/pipx?tab=readme-ov-file#install-pipx), you can either run `nox` without installing it via:

    ```bash
    pipx run nox [NOX_ARGS]
    ```

    or install `nox` into an isolated environment and run it with:

    ```bash
    pipx install nox
    nox [NOX_ARGS]
    ```

    `nox` handles everything for you, including setting up a temporary virtual environment for each task (e.g. running tests, building docs, etc.) you need to run.

Now that your development environment is set up, you can run the tests.

## Running tests

We recommend using `nox` to run the various "sessions" (`nox`'s term for tasks) provided by `earthaccess`. To use, run `nox` without
any arguments:

```bash
nox
```

This will run the type check and unit test sessions using your local (and active) Python
version. `nox` handles everything for you, including setting up a temporary virtual environment for each run.

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

You can also run individual sessions like so:

```bash
nox -s integration-tests
```

and pass options to the underlying session like:

```bash
nox -s integration-tests -- [ARGS]
```

!!! info "Important"

    In order to run integration tests locally, you must set the environment variables `EARTHDATA_USERNAME` and
    `EARTHDATA_PASSWORD` to the username and password of your [NASA Earthdata](https://urs.earthdata.nasa.gov/)
    account, respectively (registration is free).

### IDE setup

Integrated development environments (IDEs) like VS Code and PyCharm provide powerful refactoring, testing, and
debugging integrations, but they typically don't understand "task runners" like `nox` and won't know how to launch
debugging or testing sessions connected to the provided integrations.

Fortunately, if you've set up a development environment you should be able to call the underlying testing tools
(e.g., `mypy` and `pytest`) directly, or run them via your IDE integrations. To understand how `nox` is running the
underlying tools in each test session you can read the `noxfile.py` in the repository root, or, run all the test directly
in your development environment like:

```bash
nox -fb none --no-install
```

This will force `nox` to not use an environment backend (will just use the active environment) and not attempt to install
any packages. When `nox` runs, it will describe the commands it executes:

```
$ nox -fb none --no-install
nox > Running session typecheck
nox > mypy
Success: no issues found in 35 source files
nox > Session typecheck was successful.
nox > Running session tests
nox > pytest tests/unit -rxXs
========================================== test session starts ==========================================
...
==================================== 43 passed, 1 xfailed in 24.01s =====================================
nox > Session tests was successful.
nox > Ran multiple sessions:
nox > * typecheck: success
nox > * tests: success
```

Note these lines in particular:

```
nox > Running session typecheck
nox > mypy
nox > Running session tests
nox > pytest tests/unit -rxXs
```

So to reproduce the typecheck session all you have to do is run `mypy` in your development environment. Similarly, reproducing
the unit tests is running `pytest test/unit -rxXs`.

Since we're not doing any complicated configuration or setting complicated arguments to pytest, simply hitting the "play" button
for a pytest in your IDE should work once you've configured it to use your development environment.

!!! info "Important"

    Currently, our integration tests are *flakey* and a small number of random failures are expected. When the integration
    test suite runs, it may return a status code of 99 if the failure rate was less than an "acceptable" threshold. Since
    any non-zero status code is considered an error, your console and/or IDE will consider this a failure by default.
    `nox`, however, knows about this special status code and will report a success. To get pytest or your IDE to match
    this behavior, you can modify the special status code to be zero with the `EARTHACCESS_ALLOWABLE_FAILURE_STATUS_CODE`
    evnironment variable:
    ```bash
    export EARTHACCESS_ALLOWABLE_FAILURE_STATUS_CODE=0
    ```

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
nox -s serve-docs
```

MkDocs does not support incremental rebuilds and will execute every Jupyter Notebook every time it builds a new
version of the site, which can be quite slow. To speed up the build, you can pass MkDocs these options:

```
nox -s serve-docs -- --dirty --no-strict
```

!!! warning

    Our mkdocs setup has a known limitation: the hot reloader won't auto-reload when changing docstrings.
    To see updates, manually rebuild and re-serve docs. We're working to improve the developer experience and
    appreciate your patience.

### Documentation Style

To ensure that our code is well-documented and easy to understand, we use [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) to document
all functions, classes, and methods in this library.
