# Code Style Guide

This guide captures how we aspire to write code for earthaccess. It exists to make contributing easier and to keep our code readable and consistent.

## Readability first

Code is read far more often than it is written, so prioritize readability.

Write code that follows the [principle of least astonishment](https://en.wikipedia.org/wiki/Principle_of_least_astonishment): a reader should be able to tell what a function or class does from its name and signature, and the code should behave as expected, without surprises.

Follow the [single-responsibility principle](https://en.wikipedia.org/wiki/Single-responsibility_principle): give each function, method, and class one clear job. If a function does several unrelated things, split it into smaller functions.

## Naming

Names matter. We prefer clarity over succinctness. A long name that makes a purpose obvious is better than a short name that doesn't. See our [naming conventions](./naming-convention.md) for more information.

For booleans:

- Use verb-prefixed names, such as `is_cloud_hosted`, `has_granules`, or `can_download`.
- Use positive names (`is_enabled`, not `is_disabled`).
- Represent a single piece of state with a single boolean, rather than one boolean that bundles several meanings together.

## Function signatures

Use keyword-only arguments for functions and methods with more than a couple of parameters. This keeps callers explicit and makes it safe to add parameters later:

```python
def download(granules, *, local_path=None, threads=8):
    ...
```

## Docstrings

Document all public functions, classes, and methods with [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html). See the [development guide](../howto/development.md#documentation-style) for details.

## Architecture

Aim for object-oriented interfaces for stateful things, and avoid introducing new singletons.

## YAML

Quote all YAML strings defensively, even when it isn't strictly required.

## Tooling

Wherever possible, express style rules in our linter and formatter configuration rather than relying on people to remember them.

- Run fast checks in [pre-commit](../howto/development.md#usage-of-pre-commit).
- Reserve slow checks (like mypy) for CI.
- Run all checks in CI.
