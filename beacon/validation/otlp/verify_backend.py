#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compare a saved, successful Owl trace query with synthetic acceptance evidence."""

import argparse
import json
import time
from pathlib import Path


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--query-result", type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text())
    result = json.loads(args.query_result.read_text())
    check(result.get("success") is True, "the backend query did not succeed")
    data = result["data"]
    check(data.get("sample") == 1, "the query result is sampled")
    check(not data.get("sampling_required", False), "the query requires sampling")
    check(not data.get("page_info", {}).get("has_more", False), "the query is incomplete")
    spans = [row for row in data["items"] if "span_id" in row]
    check(len(spans) == len(evidence["expected_spans"]), "unexpected number of stored spans")
    by_id = {span["span_id"]: span for span in spans}
    check(len(by_id) == len(spans), "duplicate stored span IDs")
    for expected in evidence["expected_spans"]:
        check(expected["span_id"] in by_id, f"missing span: {expected['name']}")
        span = by_id[expected["span_id"]]
        check(span["trace_id"] == evidence["trace_id"], "stored trace ID changed")
        check(span["service"] == expected["service"], "stored service name changed")
        check(span["resource"] == expected["name"], "stored span name changed")
        check(int(span["parent_id"], 16) == int(expected["parent_id"], 16), "stored parent ID changed")
        check(span["sdk_language"] == "rust", "unexpected SDK language")
        check(span["source"] == "opentelemetry", "unexpected DataKit input source")
        check(span["status"] == "ok", "span has a non-OK backend status")
        check(span["duration"] >= 0, "span has a negative duration")
    by_name = {span["resource"]: span for span in spans}
    check(by_name["client.http"]["span_kind"] == "client", "client span kind changed")
    check(by_name["server.request"]["span_kind"] == "server", "server span kind changed")
    traceparent = f"00-{evidence['trace_id']}-{evidence['client']['http_span_id']}-01"
    for name in ["client.http", "server.request"]:
        extension = json.loads(by_name[name]["extension_data"])
        attributes = {item["key"]: item["value"] for item in extension["attributes"]}
        check(attributes["propagation.traceparent"]["stringValue"] == traceparent, "wire context changed")
    evidence["backend_verified"] = True
    evidence["backend_verified_ms"] = time.time_ns() // 1_000_000
    evidence["backend_span_count"] = len(spans)
    args.evidence.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"trace_id": evidence["trace_id"], "backend_verified": True, "span_count": len(spans)}))


if __name__ == "__main__":
    main()
