# Releases

Each release provides a versioned `.tar.gz` of the tracked repository at the
release commit and a `SHA256SUMS` file. The bundle includes deployment
configuration, documentation, examples, and tools; it does not include local
untracked files such as local credentials and backups, container images, or
prebuilt firmware. All tracked files are included, so never commit credentials
or other private deployment data.
GitHub also provides its own source archives, which are not covered by the
provided checksum. No package registry artifact is published: this repository
does not define a separately installable application or container image.

Download both release assets into the same directory and verify the bundle:

```sh
sha256sum --check SHA256SUMS
tar -xzf thermal-system-v1.2.3.tar.gz
```

Replace the example filename with the actual version. The checksum detects
corruption; it does not authenticate a release if both files are replaced.
Review [operations](operations.md), [safety](safety.md), and
[ESPHome setup](../esphome/README.md) before commissioning. Firmware must be
built locally after configuring site-specific credentials and sensor addresses;
CI's example binaries are not suitable for deployment.

## Preparing a release

From the reviewed commit containing the release workflow, create and push a
unique `v`-prefixed semantic-version tag, for example:

```sh
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

Prerelease tags such as `v1.2.3-rc.1` produce a GitHub prerelease. The tag must
remain on the same commit throughout the run. The workflow runs the complete
validation suite before creating a **draft** release with generated notes, the
bundle, and its checksum. It does not publish the draft automatically. A
maintainer must review the notes, assets, safety implications, and any upgrade
or commissioning instructions, then publish the draft in GitHub. Generated
notes group pull requests by the labels in `.github/release.yml`; unlabeled
changes appear in the catch-all category once that configuration is on the
default branch.

The workflow requires Actions to be enabled and permission for its
`GITHUB_TOKEN` to write repository contents. Tag creation and publication
should be restricted to authorized maintainers. Failed validation prevents a
draft from being created. If creation or asset upload is interrupted, inspect
the release and workflow logs before retrying: an existing release is not
replaced automatically. Remove an incomplete draft or repair it manually
before rerunning; never move a published release tag.
