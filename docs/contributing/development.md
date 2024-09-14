# Development

## Getting the code

1. Fork [nsidc/earthaccess](https://github.com/nsidc/earthaccess)
1. Clone your fork (`git clone git@github.com:{my-username}/earthaccess`)

In order to develop new features or fix bugs etc. we need to set up a virtual
environment and install the library locally.

## Quickstart development

The fastest way to start with development is to use nox. If you don't have nox,
you can use `pipx run nox` to run it without installing, or `pipx install nox`.
If you don't have pipx (pip for applications), then you can install with
`pip install pipx` (the only case were installing an application with regular
pip is reasonable). If you use macOS, then pipx and nox are both in brew, use
`brew install pipx nox`.

To use, run `nox`. This will typecheck and test using every installed version of
Python on your system, skipping ones that are not installed. You can also run
specific jobs:

```console
$ nox -s typecheck              # Typecheck only
$ nox -s tests                  # Python tests
$ nox -s build_docs -- --serve  # Build and serve the docs
$ nox -s build_pkg              # Make an SDist and wheel
```

Nox handles everything for you, including setting up a temporary virtual
environment for each run.

## Manual development environment setup

Create and activate a virtual environment with `venv`, which comes by default with
Python, in the `.venv` directory:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install _earthaccess_ in editable mode with optional development dependencies:

```bash
pip install --editable .[dev,test,docs]
```

## Managing Dependencies

If you need to add a new dependency, edit `pyproject.toml` and insert the dependency in
the correct location (either in the `dependencies` array or
`[project.optional-dependencies]`.
