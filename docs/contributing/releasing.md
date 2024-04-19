# Release process

> :memo: The versioning scheme we use is [SemVer](http://semver.org/). Note that until
> we agree we're ready for v1.0.0, we will not increment the major version.

1. Ensure all desired features are merged to `main` branch and `CHANGELOG.md` is updated.
1. Use `bump-my-version` to increase the version number in all needed places, e.g. to
   increase the minor version (`1.2.3` to `1.3.0`):

   ```plain
   bump-my-version bump minor
   ```

1. Push a tag on the new commit containing the version number, prefixed with `v`, e.g.
   `v1.3.0`.
1. [Create a new GitHub Release](https://github.com/nsidc/earthaccess/releases/new). We
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
