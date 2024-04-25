# Development environment setup

1. Fork [nsidc/earthaccess](https://github.com/nsidc/earthaccess)
1. Clone your fork (`git clone git@github.com:{my-username}/earthaccess`)

`earthaccess` uses Poetry to build and publish the package to PyPI, the defacto Python repository. In order to develop new features or fix bugs etc. we need to set up a virtual environment and install the library locally. We can accomplish this with Conda and Poetry, or just with Poetry.  Both workflows achieve the same result.

### Using Conda

If we have `mamba` (or `conda`) installed, we can use the environment file included in the `ci` folder. This will install all the libraries we need (including Poetry) to start developing `earthaccess`:

```bash
mamba env update -f ci/environment-dev.yml
mamba activate earthaccess-dev
poetry install
```

After activating our environment and installing the library with Poetry we can run Jupyter lab and start testing the local distribution or we can use `make` to run the tests and lint the code.
Now we can create a feature branch and push those changes to our fork!

### Using Poetry

If we want to use Poetry, first we need to [install it](https://python-poetry.org/docs/#installation). After installing Poetry we can use the same workflow we used for Conda, first we install the library locally:

```bash
poetry install
```

and now we can run the local Jupyter Lab and run the scripts etc. using Poetry:

```bash
poetry run jupyter lab
```

!!! note

    You may need to use `poetry run make ...` to run commands in the environment.

### Managing Dependencies

If you need to add a new dependency, you should do the following:

- Run `poetry add <package>` for a required (non-development) dependency
- Run `poetry add --group=dev <package>` for a development dependency, such
  as a testing or code analysis dependency

Both commands add an entry to `pyproject.toml` with a version that is
compatible with the rest of the dependencies.  However, `poetry` pins versions
with a caret (`^`), which is not what we want.  Therefore, you must locate the
new entry in `pyproject.toml` and change the `^` to `>=`.  (See
[poetry-relax](https://github.com/zanieb/poetry-relax) for the reasoning behind
this.)

In addition, you must also add a corresponding entry to
`ci/environment-mindeps.yaml`.  You'll notice in that file that required
dependencies should be pinned exactly to the versions specified in
`pyproject.toml` (after changing `^` to `>=` there), and that development
dependencies should be left unpinned.

Finally, for _development dependencies only_, you must add an entry to
`ci/environment-dev.yaml` with the same version constraint as in
`pyproject.toml`.
