# Migrating from tokio-tracing

If you're using the [tokio-tracing](https://github.com/tokio-rs/tracing) ecosystem and want to switch to fastrace for better performance, you can use [fastrace-tracing](https://github.com/fast/fastrace-tracing) to make the transition easier.

The `fastrace-tracing` crate provides a compatibility layer that lets you capture spans from libraries instrumented with `tokio-tracing` in two lines of code:

```rust
let subscriber = tracing_subscriber::Registry::default().with(fastrace_tracing::FastraceCompatLayer::new());
tracing::subscriber::set_global_default(subscriber).unwrap();
```

For more details, refer to the [fastrace-tracing documentation](https://docs.rs/fastrace-tracing).

[Documentation index](README.md)
