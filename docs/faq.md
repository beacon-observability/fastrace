# Frequently Asked Questions

## Why is Fastrace so fast?

The maintainer of fastrace posts articles describing the details:

- [The Design of A High-performance Tracing Library in Rust (Chinese)](https://www.youtube.com/watch?v=8xTaxC1RcXE)
- [How We Trace a KV Database with Less than 5% Performance Impact](https://en.pingcap.com/blog/how-we-trace-a-kv-database-with-less-than-5-percent-performance-impact/)

## What is library-level tracing?

Library-level tracing refers to the capability of incorporating tracing capabilities directly within libraries, as opposed to restricting them to application-level or system-level tracing.

Tracing can introduce overhead to a program's execution. While this is generally acceptable at the application level, where the added overhead is often insignificant compared to the overall execution time, it can be more problematic at the library level. Here, functions may be invoked frequently or performance may be critical, and the overhead from tracing can become substantial. As a result, tracing libraries not designed with speed and efficiency in mind may not be suitable for library-level tracing.

In the realm of the Fastrace library, library-level tracing is engineered to be fast and lightweight, resulting in zero overhead when it's not activated. This makes fastrace an excellent choice for use in performance-sensitive applications, and it can be seamlessly integrated into libraries in a similar fashion to the log crate, something other tracing libraries may not offer.

## How does Fastrace differ from other tracing libraries?

While many tracing libraries aim for extensive features, Fastrace prioritizes performance and simplicity.

For example, fastrace doesn't introduce new logging macros, e.g., `info!()` or `error!()`, but seamlessly integrates with the [`log`](https://crates.io/crates/log) crate. This allows you to use existing logging macros and dependencies, with logs automatically attached to the current tracing span.

## Will fastrace incorporate 'level' for spans?

The concept of 'level' may not be an optimal feature for tracing systems. While `tokio-tracing` incorporates this feature, the underlying motivation for having levels in a span primarily revolves around performance. More specifically, it relates to the performance implications of tracing elements that are not of interest. However, tracing differs from logging in two key aspects:

1. Disregarding a low-level span might inadvertently discard a high-level child span.
2. The process of filtering, or 'level' as it's often called, in a tracing system should be applied to a trace as a whole rather than individual spans within a trace.

In this context, Fastrace offers a more efficient solution by filtering out entire traces that are not of interest through its unique [tail-sampling](https://opentelemetry.io/blog/2022/tail-sampling/) design. Therefore, the concept of 'level', borrowed directly from logging systems, may not be suitable for Fastrace.

[Documentation index](README.md)
