# Reporters and Integrations

## Reporters

Fastrace supports multiple out-of-box reporters to export spans:

- [`fastrace-opentelemetry`](https://crates.io/crates/fastrace-opentelemetry): Export spans to [OpenTelemetry](https://opentelemetry.io/)

## Integrations

Fastrace provides integrations with popular libraries to handle context propagation automatically:

- [fastrace-futures](https://crates.io/crates/fastrace-futures): Trace Stream from [`futures`](https://crates.io/crates/futures)
- [fastrace-axum](https://crates.io/crates/fastrace-axum): Trace [`axum`](https://crates.io/crates/axum) HTTP services
- [fastrace-poem](https://crates.io/crates/fastrace-poem): Trace [`poem`](https://crates.io/crates/poem) HTTP services
- [fastrace-reqwest](https://crates.io/crates/fastrace-reqwest): Trace [`reqwest`](https://crates.io/crates/reqwest) HTTP requests
- [fastrace-tonic](https://crates.io/crates/fastrace-tonic): Trace [`tonic`](https://crates.io/crates/tonic) client and server requests
- [fastrace-tower](https://crates.io/crates/fastrace-tower): Trace [`tower`](https://crates.io/crates/tower) client and server requests
- [fastrace-tracing](https://crates.io/crates/fastrace-tracing): Compatibility layer for [`tracing`](https://crates.io/crates/tracing)

## Projects using fastrace

Feel free to open a PR and add your projects here:

- [Conductor](https://github.com/the-guild-org/conductor): Open-source GraphQL Gateway
- [Apache OpenDAL](https://github.com/apache/opendal): A data access layer for various storage
- [Databend](https://github.com/datafuselabs/databend): Cost-Effective alternative to Snowflake
- [foyer](https://github.com/mrcroxx/foyer): Hybrid in-memory and disk cache in Rust
- [Sail](https://github.com/lakehq/sail): Unifying stream, batch, and AI workloads with Apache Spark compatibility

[Documentation index](README.md)
