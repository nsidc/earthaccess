# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change.

Please note we have a code of conduct, please follow it in all your interactions with the project.


## Development environment


`earthaccess` is a Python library that uses Poetry to build and publish the package to PyPI, the defacto Python repository. In order to develop new features or patch bugs etc. we need to set up a virtual environment and install the library locally. We can accomplish this with both Poetry or/and Conda.

### Using Conda

If we have `mamba` (or conda) installed, we can use the environment file included in the binder folder, this will install all the libraries we need (including Poetry) to start developing `earthaccess`

```bash
>mamba env update -f binder/environment-dev.yml
>mamba activate earthaccess-dev
>poetry install
```

After activating our environment and installing the library with Poetry we can run Jupyter lab and start testing the local distribution or we can use the scripts inside `scripts` to run the tests and linting.
Now we can create a feature branch and push those changes to our fork!


### Using Poetry

If we want to use Poetry, first we need to [install it](https://python-poetry.org/docs/#installation). After installing Poetry we can use the same workflow we used for Conda, first we install the library locally:

```bash
>poetry install
```

and now we can run the local Jupyter Lab and run the scripts etc. using Poetry:

```bash
>poetry run jupyter lab
```

## First Steps to fix an issue or bug

- Read the documentation (working on adding more)
- create the minimally reproducible issue
- try to edit the relevant code and see if it fixes it
- submit the fix to the problem as a pull request
- include an explanation of what you did and why

## First steps to contribute new features

- Create an issue to discuss the feature's scope and its fit for this package
- run pytest to ensure your local version of code passes all unit tests
- try to edit the relevant code and implement your new feature in a backwards compatible manner
- create new tests as you go, and run the test suite as you go
- update the documentation as you go

### Please format and lint as you go with the following scripts

```bash
scripts/lint.sh
scripts/format.sh
```

### Requirements to merge code (Pull Request Process)

- you must include test coverage
- you must update the documentation
- you must run the above scripts to format and line

## Pull Request process

1. Ensure you include test coverage for all changes
2. Ensure your code is formatted properly following this document
3. Update the documentation and the README.md with details of changes to the interface,
   this includes new environment variables, function names, decorators, etc.
3. Update `CHANGELOG.md` with details about your change in a section titled
   `Unreleased`. If one does not exist, please create one.
4. You may merge the Pull Request in once you have the sign-off of another developers,
   or if you do not have permission to do that, you may request the reviewer to merge it
   for you.

## Release process

> :memo: The versioning scheme we use is [SemVer](http://semver.org/). Note that until
> we agree we're ready for v1.0.0, we will not increment major version.

0. Ensure all desired features are merged to `main` branch and `CHANGELOG` is updated.
1. Use `bump-my-version` to increase the version number in all needed places, e.g. to
   increase the minor version (`1.2.3` to `1.3.0`):
   ```
   bump-my-version bump minor
   ```
2. Push a tag on the new commit containing the version number, prefixed with `v`, e.g.
   `v1.3.0`.
3. [Create a new GitHub Release](https://github.com/nsidc/earthaccess/releases/new). We
   hand-curate our release notes to be valuable to humans. Please do not auto-generate
   release notes and aim for consistency with the GitHub Release descriptions from other
   releases.

> :gear: After the GitHub release is published, multiple automations will trigger:
>
> - Zenodo will create a new DOI.
> - GitHub Actions will publish a PyPI release.

> :memo: `earthaccess` is published to conda-forge through the
> [earthdata-feedstock](https://github.com/conda-forge/earthdata-feedstock), as this
> project was renamed early in its life. The conda package is named `earthaccess`.

##  Steps to make changes to documentation
1. Fork [earthaccess](https://github.com/nsidc/earthaccess) in the GitHub user interface to create your own copy. Later on, you may need to sync your fork with the upstream original repository. This can also be done in the GitHub UI or command line. If you get stuck, the emergency escape hatch is to take a fresh fork again! :)
2. Clone the repo: `git clone git@github.com:<yourusername>/earthaccess.git`
3. Change the directory: `cd earthaccess\binder`
4. Create conda environment: `conda env create -f environment-dev.yml`. If you see a warning that the environment already exists, do `conda env remove -n earthaccess-dev`
5. Activate conda: `conda activate earthaccess-dev`
6. Change to the base project directory. `cd ..`
7. Install packages : `pip install --editable .`
8. Run mkdocs script: `./scripts/docs-live.sh`
10. On your browser, go to: `https://0.0.0.0:8008`
11. You can now change any pages in the `docs` folder in your text editor, which will instantly reflect in the browser.
12. Commit the changes and push them to the forked repository:
```bash
git status # check git status to see what changed
git switch -c "test" # create a new branch
git add . # add changes
git commit -m "add commit messages" # commit changes
git push -u origin test # push changes
```
13. Open a pull request (PR) in the GitHub user interface from your fork to the original `nsidc/earthaccess` repo. When you ran `git push` in a previous step, it provided a convenient link to open that PR directly.
14. In the PR interface, you can view the progress of the GitHub Actions workflows specific to the PR at the bottom of the page.

---

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment
include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

- The use of sexualized language or imagery and unwelcome sexual attention or
advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or electronic
  address, without explicit permission
- Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

### Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team at betolink@pm.me. All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

### Attribution

This Code of Conduct is adapted from the [PurpleBooth's Contributing Template][contributing-template-url]

[contributing-template-url]: https://gist.github.com/PurpleBooth/b24679402957c63ec426/5c4f62c1e50c1e6654e76e873aba3df2b0cdeea2
