// SPDX-License-Identifier: Apache-2.0

use std::borrow::Cow;
use std::error::Error;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::time::Duration;

use fastrace::collector::{Config, W3CTraceContext};
use fastrace::prelude::*;
use opentelemetry_otlp::WithExportConfig;

type Result<T> = std::result::Result<T, Box<dyn Error>>;

fn initialize(endpoint: &str, service: &str) -> Result<()> {
    let exporter = opentelemetry_otlp::SpanExporter::builder()
        .with_tonic()
        .with_endpoint(endpoint)
        .with_timeout(Duration::from_secs(5))
        .build()?;
    let reporter = fastrace_opentelemetry::OpenTelemetryReporter::new(
        exporter,
        Cow::Owned(
            opentelemetry_sdk::Resource::builder()
                .with_service_name(service.to_owned())
                .build(),
        ),
        opentelemetry::InstrumentationScope::builder("fastrace-otlp-acceptance").build(),
    );
    fastrace::set_reporter(
        reporter,
        Config::default().report_interval(Duration::from_secs(60)),
    );
    Ok(())
}

fn request_headers(stream: &mut TcpStream) -> Result<String> {
    stream.set_read_timeout(Some(Duration::from_secs(10)))?;
    stream.set_write_timeout(Some(Duration::from_secs(10)))?;
    let mut bytes = Vec::new();
    let mut byte = [0];
    while !bytes.ends_with(b"\r\n\r\n") {
        if bytes.len() >= 8192 || stream.read(&mut byte)? == 0 {
            return Err("incomplete or oversized HTTP headers".into());
        }
        bytes.push(byte[0]);
    }
    Ok(String::from_utf8(bytes)?)
}

fn server(endpoint: &str) -> Result<()> {
    initialize(endpoint, "fastrace-e2e-server")?;
    let listener = TcpListener::bind("127.0.0.1:0")?;
    println!("LISTENING {}", listener.local_addr()?);
    std::io::stdout().flush()?;
    let (mut stream, _) = listener.accept()?;
    let request = request_headers(&mut stream)?;
    let headers: Vec<_> = request
        .lines()
        .filter_map(|line| line.split_once(':'))
        .map(|(name, value)| (name.trim(), value.trim()))
        .collect();
    let context = W3CTraceContext::decode_headers(headers.iter().copied())
        .ok_or("missing or invalid traceparent")?;
    if context.tracestate() != Some("beacon=e2e") {
        return Err("tracestate was not propagated".into());
    }
    let incoming = context.encode_traceparent();
    let root = Span::root("server.request", context.span_context)
        .with_property(|| ("span.kind", "server"))
        .with_property(|| ("span.parent_span_is_remote", "true"))
        .with_property(|| ("propagation.traceparent", incoming));
    let root_context = SpanContext::from_span(&root).ok_or("missing server root context")?;
    let work = Span::enter_with_parent("server.work", &root);
    let work_context = SpanContext::from_span(&work).ok_or("missing server work context")?;
    drop(work);
    let body = context.span_context.trace_id.to_string();
    write!(
        stream,
        "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        body.len(),
        body
    )?;
    drop(stream);
    drop(root);
    fastrace::flush();
    println!(
        "{{\"mode\":\"server\",\"trace_id\":\"{}\",\"span_id\":\"{}\",\"parent_id\":\"{}\",\"work_span_id\":\"{}\",\"tracestate\":\"beacon=e2e\",\"flushed\":true}}",
        root_context.trace_id,
        root_context.span_id,
        context.span_context.span_id,
        work_context.span_id,
    );
    Ok(())
}

fn client(endpoint: &str, address: &str) -> Result<()> {
    initialize(endpoint, "fastrace-e2e-client")?;
    let root = Span::root("client.request", SpanContext::random());
    let root_context = SpanContext::from_span(&root).ok_or("missing client root context")?;
    let outgoing =
        Span::enter_with_parent("client.http", &root).with_property(|| ("span.kind", "client"));
    let span_context = SpanContext::from_span(&outgoing).ok_or("missing outgoing context")?;
    let wire_context = W3CTraceContext::new(span_context).with_tracestate("beacon=e2e");
    let traceparent = wire_context.encode_traceparent();
    let outgoing = outgoing.with_property(|| ("propagation.traceparent", traceparent));
    let mut stream = TcpStream::connect(address)?;
    stream.set_read_timeout(Some(Duration::from_secs(10)))?;
    stream.set_write_timeout(Some(Duration::from_secs(10)))?;
    write!(stream, "GET /acceptance HTTP/1.1\r\nHost: {address}\r\n")?;
    for (name, value) in wire_context.encode_headers() {
        write!(stream, "{name}: {value}\r\n")?;
    }
    write!(stream, "Connection: close\r\n\r\n")?;
    let mut response = String::new();
    stream.read_to_string(&mut response)?;
    let expected_body = format!("\r\n\r\n{}", root_context.trace_id);
    if !response.starts_with("HTTP/1.1 200 OK\r\n") || !response.ends_with(&expected_body) {
        return Err("downstream did not return the propagated trace ID".into());
    }
    drop(outgoing);
    let last = Span::enter_with_parent("client.before_exit", &root);
    let last_context = SpanContext::from_span(&last).ok_or("missing final span context")?;
    drop(last);
    drop(root);
    fastrace::flush();
    println!(
        "{{\"mode\":\"client\",\"trace_id\":\"{}\",\"root_span_id\":\"{}\",\"http_span_id\":\"{}\",\"before_exit_span_id\":\"{}\",\"flushed\":true}}",
        root_context.trace_id, root_context.span_id, span_context.span_id, last_context.span_id,
    );
    Ok(())
}

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    match args.as_slice() {
        [_, mode, endpoint] if mode == "server" => server(endpoint),
        [_, mode, endpoint, address] if mode == "client" => client(endpoint, address),
        _ => {
            Err("usage: fastrace-otlp-acceptance server ENDPOINT | client ENDPOINT ADDRESS".into())
        }
    }
}
