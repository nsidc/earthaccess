# Contributing Naming Convention

## General Guidelines

This document outlines the naming conventions for our project. These conventions are intended to promote consistency and clarity across different components.

### Specific Conventions

#### Python Code

* **Style**: We follow Python Enhancement Proposal 8 ([PEP8](https://peps.python.org/pep-0008/#package-and-module-names)) guidelines for naming conventions.

#### Jupyter Notebooks

* **File names**: Please use underscores (`_`) instead of hyphens (`-`).

#### Documentation

* **Directory and file names**: Directory names and Markdown file names should use hyphens (`-`) instead of underscores (`_`).

#### Tests

1. **Test file and member names**: Test files and methods should start with `test_`. Classes should start with `Test`.

    !!! note "Test File Naming Convention"
        We do not use the _test.py suffix for test files

2. **Additional Guidelines**: For additional guidelines, please refer to the [pytest documentation](https://docs.pytest.org/en/stable/explanation/goodpractices.html#conventions-for-python-test-discovery).
