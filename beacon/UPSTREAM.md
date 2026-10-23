# Upstream baseline

Based on [fast/fastrace](https://github.com/fast/fastrace).

Adopted source commit: `45e58b94264dd2134b4b08be36f8378a4539bb50`.

This is an independent source snapshot, without a GitHub fork relationship or shared upstream commit ancestry. Original copyright, crate identities, and [Apache-2.0](../LICENSE) are retained. Upstream README content is organized by topic in [docs](../docs/README.md).

## Synchronization

1. Fetch the upstream remote; review an exact target commit.
2. Save `git diff --binary --full-index <baseline> <target> -- . ':!README.md'` outside the checkout.
3. On a clean synchronization branch, use `git apply --3way <patch>`; resolve conflicts and retain Beacon changes. Apply upstream README edits to the corresponding guides under docs/, retaining the project README attribution and documentation index.
4. Run relevant [checks](../CONTRIBUTING.md), update this baseline, and submit a PR. Successful application alone is not validation.

Initial changes are documentation only; there is no independent Beacon release.
