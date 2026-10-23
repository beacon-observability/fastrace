# Source Release Maintenance

Fastrace is a Rust SDK distributed as source. Beacon release versions are independent of the crate versions retained from the [upstream baseline](UPSTREAM.md). GitHub is the release channel. Publishing upstream-named packages to crates.io requires separately verified ownership and authorization.

## Prepare and validate

1. Select an unused release tag, review upstream provenance and licenses, and commit the final English installation and release documentation. Keep the SDK name `fastrace`; a possible future `beacon-rust` is a separate project.
2. Run the existing CI matrix on the exact candidate commit. Record the successful run URL. The matrix covers Rust 1.91.0, stable, and nightly on Linux, macOS, and Windows, plus formatting and lint checks.
3. Create an annotated local tag on that commit. Do not move a published tag or replace published artifacts.
4. Build the source asset from the tag, outside the checkout. For v0.1.0:

   ```sh
   git archive --format=tar --prefix=fastrace-0.1.0/ v0.1.0 | gzip -n > /path/to/assets/fastrace-0.1.0-source.tar.gz
   ```

5. Create `release-manifest.json` recording the release tag and exact source commit, upstream URL and full baseline commit, retained crate versions, license, SHA-256 hashes of committed lockfiles, packaging tool versions, CI evidence, and acceptance scope. This is a maintainer-created provenance record, not a signed attestation.
6. In the assets directory, create `SHA256SUMS` for the source archive and manifest. Check it, unpack the archive into a new directory, and build with committed lockfiles. Run a separate consumer using dependencies from the candidate Git revision and confirm that all Fastrace crates resolve from that revision. Run the two-process [DataKit acceptance](../docs/validation.md) from the archive and verify stored backend records. Record exact toolchain, receiver, protocol, time range, and trace ID in the release notes.

## Publish and verify

Push the annotated tag only after validation succeeds. Create a GitHub draft release with the tested assets and English notes; specify the source commit and tag explicitly. The notes must distinguish the Beacon source version from upstream crate versions, list validation and known limitations, and link the version-pinned installation and rollback instructions.

Download the draft assets and compare their hashes with the tested files before publishing. Publish the draft as the latest release only when those checks pass. Then download assets from the public release into a fresh directory, verify `SHA256SUMS`, build and run from that source, and run a consumer using the published Git tag. Retain local test records and reference the public acceptance evidence in release notes.

Update the Beacon [language index](https://github.com/beacon-observability/beacon/blob/main/docs/languages.md#rust) and organization profile with the actual release and version-pinned installation entry. Keep detailed Rust build, synchronization, and validation records here.

If publication fails, inspect the existing draft and uploaded files before retrying. After publication, issue a new version for corrections to source or artifacts. Document upgrades and rollback in the [installation guide](../docs/installation.md#upgrade-and-rollback).
