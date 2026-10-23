# DataKit OTLP Acceptance

This development acceptance sends a synthetic trace from two independent Rust processes to a local DataKit OTLP/gRPC receiver. It verifies stored backend records rather than treating exporter completion as proof of ingestion. It does not define an independent Beacon release.

## Reproduce

Requirements: a Rust toolchain meeting the repository MSRV, Python 3.9 or newer on Linux, and a running local DataKit with its OpenTelemetry gRPC receiver enabled. The default endpoint is `http://127.0.0.1:4317`; the status API is `http://127.0.0.1:9529/v1/ping`.

From the repository root:

```sh
python3 beacon/validation/otlp/run.py --output /tmp/fastrace-datakit-acceptance
```

The runner builds the isolated acceptance crate using its committed lockfile, starts a one-request HTTP server in one process, and sends a request from a second process. It injects and extracts W3C `traceparent` and `tracestate`, creates a final `client.before_exit` span, and calls `fastrace::flush()` in both processes. Synthetic service names are `fastrace-e2e-client` and `fastrace-e2e-server`.

The initial `evidence.json` deliberately has `backend_verified: false`. Query the backend for the exact trace ID and absolute time window in that file. With Owl, discover the trace namespace using `owl.data.show_dql_namespace`, validate the query using `owl.data.check_dql`, then execute `owl.data.query`. Pass typed parameters through JSON (`-p`) so the `T` namespace stays a string. Read the saved result file and confirm its internal success field.

Verify the saved backend response against the process evidence:

```sh
python3 beacon/validation/otlp/verify_backend.py \
  --evidence /tmp/fastrace-datakit-acceptance/evidence.json \
  --query-result /path/to/saved-backend-response.json
```

Only this second step sets `backend_verified: true`. It rejects missing or duplicated spans, incorrect service names, changed trace or parent IDs, incorrect client/server kinds, incomplete or sampled query results, and altered recorded `traceparent` values. DataKit may normalize the root parent ID to `0`; the verifier compares zero values numerically.

## Acceptance record: 2026-10-23

- Application source: [Fastrace source revision c01f0b5](https://github.com/beacon-observability/fastrace/tree/c01f0b507aa12339d69bb6226056ae6850479f1c), plus the acceptance harness included with this record. Core SDK and reporter code were unchanged.
- Build toolchain: Rust/Cargo 1.95.0; OpenTelemetry dependencies 0.33.1, resolved by the harness lockfile.
- Receiver: DataKit 1.94.2, commit `2ddc51d543`, at `http://127.0.0.1:4317` using OTLP/gRPC.
- Trace activity: 2026-10-23T08:28:10.779Z through 2026-10-23T08:28:10.847Z.
- Backend query window: 2026-10-23T08:28:05.779Z through 2026-10-23T08:29:03.710Z.
- Data domain and tools: tracing namespace `T`; `owl.data.check_dql` followed by `owl.data.query`.
- Synthetic trace ID: `eabc1e8a607e1375576010c54c843bfb`.
- Result: all five expected spans were stored, with the original 128-bit trace ID, exact span IDs, service names, and parent relationships. The backend query was successful, complete, and unsampled. The final pre-exit span was present after both processes flushed and exited.

| Span | Service | Span ID | Expected parent ID |
| --- | --- | --- | --- |
| client.request | fastrace-e2e-client | `c0ce78e500000001` | `0000000000000000` |
| client.http | fastrace-e2e-client | `c0ce78e500000002` | `c0ce78e500000001` |
| client.before_exit | fastrace-e2e-client | `c0ce78e500000003` | `c0ce78e500000001` |
| server.request | fastrace-e2e-server | `c775fccd00000001` | `c0ce78e500000002` |
| server.work | fastrace-e2e-server | `c775fccd00000002` | `c775fccd00000001` |

The backend also preserved the same `propagation.traceparent` attribute on the client and server request spans. The HTTP boundary test explicitly passed `tracestate: beacon=e2e`; this demonstrates boundary encoding/decoding, not automatic preservation through the internal span machinery. See [trace context implementation](../crates/fastrace/src/collector/id.rs).

This result covers a source checkout and the local DataKit OTLP/gRPC path. It does not establish a published package or other receiver/protocol support. Continue to validate the declared scope when changing the upstream baseline or reporter dependencies.
