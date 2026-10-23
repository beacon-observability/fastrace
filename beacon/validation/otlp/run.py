#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Send a synthetic two-process trace to a local DataKit OTLP/gRPC receiver."""

import argparse
import json
import re
import select
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:4317")
    parser.add_argument("--datakit-status-url", default="http://127.0.0.1:9529/v1/ping")
    parser.add_argument("--binary", type=Path, help="Use an already-built acceptance binary")
    parser.add_argument("--output", type=Path, help="Directory for synthetic acceptance evidence")
    parser.add_argument("--toolchain", default="stable")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    output = args.output or Path(tempfile.mkdtemp(prefix="fastrace-datakit-"))
    output.mkdir(parents=True, exist_ok=True)

    with urlopen(args.datakit_status_url, timeout=5) as response:
        datakit = json.load(response)["content"]
    endpoint = urlparse(args.endpoint)
    check(endpoint.hostname is not None, "endpoint must include a hostname")
    with socket.create_connection((endpoint.hostname, endpoint.port or 4317), timeout=5):
        pass

    binary = args.binary
    if binary is None:
        manifest = directory / "Cargo.toml"
        cargo = ["cargo", f"+{args.toolchain}"]
        subprocess.run(
            cargo + ["build", "--locked", "--manifest-path", str(manifest)],
            check=True,
            timeout=300,
        )
        metadata = json.loads(subprocess.check_output(
            cargo + ["metadata", "--no-deps", "--format-version", "1", "--manifest-path", str(manifest)],
            text=True,
        ))
        binary = Path(metadata["target_directory"]) / "debug/fastrace-otlp-acceptance"

    start_ms = time.time_ns() // 1_000_000
    with (output / "server.stderr").open("w") as server_errors:
        server = subprocess.Popen(
            [str(binary), "server", args.endpoint],
            stdout=subprocess.PIPE,
            stderr=server_errors,
            text=True,
        )
        try:
            readable, _, _ = select.select([server.stdout], [], [], 15)
            check(readable, "server did not announce an HTTP listener")
            listener = server.stdout.readline().strip()
            check(listener.startswith("LISTENING "), "server failed before starting its HTTP listener")
            address = listener.removeprefix("LISTENING ")
            client = subprocess.run(
                [str(binary), "client", args.endpoint, address],
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
            server_output, _ = server.communicate(timeout=20)
            check(server.returncode == 0, "server process failed; inspect server.stderr")
            client_result = json.loads(client.stdout.strip())
            server_result = json.loads(server_output.strip())
        finally:
            if server.poll() is None:
                server.terminate()
                server.communicate(timeout=5)

    trace_id = client_result["trace_id"]
    check(re.fullmatch("[0-9a-f]{32}", trace_id) and int(trace_id, 16), "invalid trace ID")
    check(server_result["trace_id"] == trace_id, "cross-process trace ID changed")
    check(server_result["parent_id"] == client_result["http_span_id"], "remote parent ID changed")
    check(server_result["tracestate"] == "beacon=e2e", "tracestate header was lost")
    check(client_result["flushed"] and server_result["flushed"], "a process did not flush")
    expected_spans = [
        ("client.request", "fastrace-e2e-client", client_result["root_span_id"], "0" * 16),
        ("client.http", "fastrace-e2e-client", client_result["http_span_id"], client_result["root_span_id"]),
        ("client.before_exit", "fastrace-e2e-client", client_result["before_exit_span_id"], client_result["root_span_id"]),
        ("server.request", "fastrace-e2e-server", server_result["span_id"], client_result["http_span_id"]),
        ("server.work", "fastrace-e2e-server", server_result["work_span_id"], server_result["span_id"]),
    ]
    for _, _, span_id, _ in expected_spans:
        check(re.fullmatch("[0-9a-f]{16}", span_id) and int(span_id, 16), "invalid span ID")
    evidence = {
        "receiver": "DataKit",
        "endpoint": args.endpoint,
        "datakit_version": datakit["version"],
        "datakit_commit": datakit["commit"],
        "protocol": "OTLP/gRPC",
        "start_ms": start_ms,
        "end_ms": time.time_ns() // 1_000_000,
        "trace_id": trace_id,
        "client": client_result,
        "server": server_result,
        "expected_spans": [
            dict(name=name, service=service, span_id=span_id, parent_id=parent_id)
            for name, service, span_id, parent_id in expected_spans
        ],
        "backend_verified": False,
    }
    destination = output / "evidence.json"
    destination.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"trace_id": trace_id, "evidence": str(destination), "backend_verified": False}))


if __name__ == "__main__":
    main()
