"""Check independent expectations from the original HTTP tests."""

import argparse
import base64
import json
from pathlib import Path

from evaluate import TARGET, REPOSITORY, compare, save
from fixture import start


def vectors(url):
    text = "hello\n"
    post = {"method": "POST", "path": "/text", "body": '{"name":"ali"}', "headers": {"content-type": ["application/json"]}}
    return [
        {"test": "basic_json_post", "args": ["POST", url + "/text", "name=ali"], "stdout": text, "requests": [post]},
        {"test": "basic_get", "args": ["get", url + "/text"], "stdout": text, "requests": [{"method": "GET", "path": "/text", "body": ""}]},
        {"test": "basic_head", "args": ["head", url + "/text"], "stdout": "", "requests": [{"method": "HEAD", "path": "/text", "body": ""}]},
        {"test": "post_empty_body", "args": ["post", url + "/text"], "stdout": text, "requests": [{"method": "POST", "path": "/text", "body": "", "absent_headers": ["transfer-encoding"]}]},
        {"test": "header", "args": [url + "/text", "x-foo:Bar"], "stdout": text, "requests": [{"method": "GET", "path": "/text", "body": "", "headers": {"x-foo": ["Bar"]}}]},
        {"test": "multiple_headers_with_same_key", "args": [url + "/text", "hello:world", "hello:people"], "stdout": text, "requests": [{"method": "GET", "path": "/text", "body": "", "headers": {"hello": ["world", "people"]}}]},
        {"test": "json_param", "args": [url + "/text", "foo:=[1,2,3]"], "stdout": text, "requests": [{"method": "POST", "path": "/text", "body": '{"foo":[1,2,3]}'}]},
        {"test": "forced_json", "args": ["--json", url + "/text"], "stdout": text, "requests": [{"method": "GET", "path": "/text", "body": "", "headers": {"accept": ["application/json, */*;q=0.5"], "content-type": ["application/json"]}}]},
        {"test": "body_from_raw", "args": ["--raw=body from raw", url + "/text"], "stdout": text, "requests": [{"method": "POST", "path": "/text", "body": "body from raw"}]},
        {"test": "request_json_keys_order_is_preserved", "args": ["get", url + "/text", "name=ali", "age:=24"], "stdout": text, "requests": [{"method": "GET", "path": "/text", "body": '{"name":"ali","age":24}'}]},
        {"test": "check_status_warning", "args": ["--check-status", url + "/status/501"], "stdout": "status 501\n", "stderr": "xh: warning: HTTP 501 Not Implemented\n", "returncode": 5, "requests": [{"method": "GET", "path": "/status/501", "body": ""}]},
        {"test": "method_is_changed_when_following_302_redirect", "args": ["post", url + "/upstream-redirect/302", "--follow", "name=ali"], "stdout": text, "requests": [{**post, "path": "/upstream-redirect/302"}, {"method": "GET", "path": "/text", "body": "", "absent_headers": ["content-length", "content-type"]}]},
        {"test": "method_is_not_changed_when_following_307_redirect", "args": ["post", url + "/upstream-redirect/307", "--follow", "name=ali"], "stdout": text, "requests": [{**post, "path": "/upstream-redirect/307"}, post]},
    ]


def failures(vector, output, requests):
    errors = []
    for field, expected in (("returncode", vector.get("returncode", 0)), ("stdout_b64", base64.b64encode(vector["stdout"].encode()).decode()), ("stderr_b64", base64.b64encode(vector.get("stderr", "").encode()).decode()), ("error", None)):
        if output[field] != expected:
            errors.append(field)
    if len(requests) != len(vector["requests"]):
        errors.append("request_count")
    for index, (actual, expected) in enumerate(zip(requests, vector["requests"])):
        for field in ("method", "path"):
            if actual[field] != expected[field]:
                errors.append(f"request_{index}_{field}")
        if actual["body_b64"] != base64.b64encode(expected["body"].encode()).decode():
            errors.append(f"request_{index}_body")
        headers = {}
        for name, value in actual["headers"]:
            headers.setdefault(name.lower(), []).append(value)
        for name, values in expected.get("headers", {}).items():
            if headers.get(name) != values:
                errors.append(f"request_{index}_header_{name}")
        for name in expected.get("absent_headers", []):
            if name in headers:
                errors.append(f"request_{index}_unexpected_header_{name}")
    return errors


def evaluate(reference, candidate):
    server = start()
    records = []
    try:
        for vector in vectors(f"http://127.0.0.1:{server.server_port}"):
            case = {"id": vector["test"], "args": ["--body", "--pretty=none", "--ignore-stdin", *vector["args"]]}
            record = {"test": vector["test"], "expected": vector, "input": case}
            for label, binary in (("reference", reference), ("candidate", candidate)):
                server.requests.clear()
                result = compare.run(binary, "xh", case, 5)
                requests = server.requests.copy()
                record[label] = {"result": result, "requests": requests, "failures": failures(vector, result, requests)}
            record["passed"] = not record["reference"]["failures"] and not record["candidate"]["failures"]
            records.append(record)
    finally:
        server.shutdown()
        server.server_close()
    return {"status": "passed" if all(record["passed"] for record in records) else "failed", "passed": sum(record["passed"] for record in records), "failed": sum(not record["passed"] for record in records), "cases": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=REPOSITORY / "work/downloads/xh")
    parser.add_argument("--candidate", type=Path, default=TARGET / "implementation/target/debug/xh")
    parser.add_argument("--report", type=Path, default=TARGET / "verification/raw/upstream.json")
    args = parser.parse_args()
    report = evaluate(args.reference.resolve(), args.candidate.resolve())
    save(args.report, report)
    print(json.dumps({key: report[key] for key in ("status", "passed", "failed")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
