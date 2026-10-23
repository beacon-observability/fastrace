# Beacon Source Installation

Based on [fast/fastrace](https://github.com/fast/fastrace). Beacon source release **v0.1.0** uses upstream baseline `45e58b94264dd2134b4b08be36f8378a4539bb50` and retains Apache-2.0. The release version identifies the Beacon source distribution. The contained crate versions remain `fastrace`, `fastrace-macro`, and `fastrace-futures` 0.7.19, and `fastrace-opentelemetry` 0.19.0.

## Install from a fixed Git tag

Use Rust 1.91.0 or newer. Applications must enable collection explicitly:

```toml
[dependencies]
fastrace = { git = "https://github.com/beacon-observability/fastrace.git", tag = "v0.1.0", features = ["enable"] }
fastrace-opentelemetry = { git = "https://github.com/beacon-observability/fastrace.git", tag = "v0.1.0" }
```

Add `fastrace-futures` from the same Git URL and tag when using that integration. Libraries should omit the `enable` feature and leave the collection decision to the application. Cargo resolves workspace path dependencies, including `fastrace-macro`, from the same Git revision. Commit your application's `Cargo.lock` and use `cargo build --locked` in reproducible builds. Check `cargo tree` for duplicate Fastrace sources if other dependencies use crates.io; registry and Git packages are distinct Cargo identities and their span types must not be mixed.

This release publishes source on GitHub. Installing `fastrace = "0.7"` from crates.io selects the upstream distribution. No Beacon-owned crates.io package or prebuilt agent executable is published in this release. Source manifest repository and API documentation metadata are retained from the upstream baseline.

## Download and verify the source archive

The [v0.1.0 release](https://github.com/beacon-observability/fastrace/releases/tag/v0.1.0) provides `fastrace-0.1.0-source.tar.gz`, `release-manifest.json`, and `SHA256SUMS`. Download all three assets into an empty directory, then run:

```sh
sha256sum --check SHA256SUMS
tar -xzf fastrace-0.1.0-source.tar.gz
cd fastrace-0.1.0
cargo +stable build --locked --workspace --all-features
```

The manifest records the release commit, upstream baseline, crate versions, and committed lockfile hashes. Check it against the Git tag and archive contents. Checksums verify consistency with the release assets; they are not a signature or build attestation. Cargo needs access to dependency sources; the archive does not vendor third-party crates.

Applications may alternatively use path dependencies to `crates/fastrace` and `crates/fastrace-opentelemetry` inside this verified archive. Use one source consistently for all Fastrace crates.

## Report to local DataKit

The validated receiver is DataKit **1.94.2** with its OpenTelemetry gRPC receiver enabled on **`http://127.0.0.1:4317`**. Export uses **OTLP/gRPC with Protobuf** through `fastrace-opentelemetry` and `opentelemetry-otlp` 0.33.1. Configure that endpoint on the exporter explicitly. A container must have network access to the receiver; its loopback address refers to the container itself.

Initialize the reporter inside a Tokio runtime, configure a service name, and enable Fastrace collection. Close root spans and call `fastrace::flush()` before process exit. See the [complete working exporter and HTTP propagation example](../beacon/validation/otlp/src/main.rs), its [dependency manifest](../beacon/validation/otlp/Cargo.toml), and [acceptance instructions](validation.md).

To run the two-process synthetic example from the release source:

```sh
python3 beacon/validation/otlp/run.py --output /tmp/fastrace-datakit-acceptance
```

This requires Python 3.9 or newer on Linux and a running DataKit status API at `http://127.0.0.1:9529/v1/ping`. The runner uses its committed lockfile. Successful exporter exit alone does not prove ingestion; verify the five stored spans using the procedure in the acceptance guide.

Trace IDs are 128-bit values and span IDs are 64-bit values. The example explicitly injects and extracts W3C `traceparent` and `tracestate` at the HTTP boundary. Internal spans do not automatically retain arbitrary `tracestate`. The validated ingestion scope is traces through local DataKit OTLP/gRPC on Linux; metrics, logs, automatic instrumentation, and other receiver/protocol combinations are outside this acceptance.

## Upgrade and rollback

Before upgrading, review the target release notes, baseline, dependencies, and limitations. Update all Fastrace Git dependencies to the same fixed tag, update the application lockfile, rebuild, and repeat the DataKit acceptance for your application. Keep the previous manifest, lockfile, and application artifact so rollback restores the exact prior dependency graph. v0.1.0 is the first Beacon source release; there is no earlier Beacon release to roll back to. To undo initial adoption, restore your application's previous dependency files and rebuild that version.

[Documentation index](README.md)
