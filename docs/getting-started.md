# Getting Started

## In Libraries

Libraries should include `fastrace` as a dependency without enabling any extra features.

```toml
[dependencies]
fastrace = "0.7"
```

Add a `trace` attribute to the function you want to trace. In this example, a `SpanRecord` will be collected every time the function is called, if the caller sets up a tracing context.

```rust
#[fastrace::trace]
pub fn send_request(req: HttpRequest) -> Result<(), Error> {
    // ...
}
```

Libraries can set up an individual tracing context, regardless of whether the caller has already set up a tracing context or not. This can be achieved by using `Span::root()` to start a new trace and `Span::set_local_parent()` to set up a local context for the current thread.

The `func_path!()` macro can detect the function's full name, which is used as the name of the root span.

```rust
use fastrace::prelude::*;

pub fn send_request(req: HttpRequest) -> Result<(), Error> {
    let root = Span::root(func_path!(), SpanContext::random());
    let _guard = root.set_local_parent();

    // ...
}
```

## In Applications

Applications should include `fastrace` as a dependency with the `enable` feature set. To disable `fastrace` statically, remove the `enable` feature.

```toml
[dependencies]
fastrace = { version = "0.7", features = ["enable"] }
```

Applications should initialize a `Reporter` implementation early in the program's runtime. Span records generated before the reporter is initialized will be ignored. Before terminating, `flush()` should be called to ensure all collected span records are reported.

When the root span is dropped, all of its children spans and itself will be reported at once. Since then, it's recommended to create root spans for short tasks, such as handling a request, as shown in the example below. Otherwise, an endless trace will never be reported.

```rust
use fastrace::collector::Config;
use fastrace::collector::ConsoleReporter;
use fastrace::prelude::*;

fn main() {
    fastrace::set_reporter(ConsoleReporter, Config::default());

    loop {
        let root = Span::root("worker-loop", SpanContext::random());
        let _guard = root.set_local_parent();

        handle_request();
    }

    fastrace::flush();
}
```

## Supported Rust Versions (MSRV 1.91.0)

Fastrace is built against the latest stable release. The minimum supported version is 1.91.0. The current Fastrace version is not guaranteed to build on Rust versions earlier than the minimum supported version.

[Documentation index](README.md)
