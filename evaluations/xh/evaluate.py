"""Compare the clients and their requests on a loopback HTTP fixture."""

import argparse
import importlib.util
import json
from pathlib import Path

from fixture import start


ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "target"
REPOSITORY = ROOT.parents[1]
HELPER = REPOSITORY / "skills/rustify-validate/scripts/compare.py"
SPEC = importlib.util.spec_from_file_location("compare", HELPER)
compare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)


def cases(url):
    rows = [
        ("get-text", [url + "/text"]),
        ("get-json", [url + "/json"]),
        ("get-query", [url + "/echo?q=two%20words&n=2"]),
        ("head", ["HEAD", url + "/echo"]),
        ("empty-post", ["POST", url + "/echo"]),
        ("json-fields", ["POST", url + "/echo", "hello=world", "count:=2"]),
        ("json-types", ["POST", url + "/echo", "active:=true", "items:=[1,2]", "value:=null"]),
        ("json-order", ["POST", url + "/echo", "z=last", "a=first"]),
        ("json-replace", ["POST", url + "/echo", "a=first", "a=last"]),
        ("inferred-post", [url + "/echo", "hello=world"]),
        ("raw-post", ["POST", url + "/echo", "--raw", "plain text"]),
        ("raw-empty", [url + "/echo", "--raw", ""]),
        ("json-get", ["--json", url + "/echo"]),
        ("custom-header", [url + "/echo", "X-Test:two words"]),
        ("header-equals", [url + "/echo", "X-Test:a=b"]),
        ("string-operator", [url + "/echo", "a=foo:=bar"]),
        ("custom-accept", [url + "/echo", "Accept:text/plain"]),
        ("custom-content-type", ["POST", url + "/echo", "--raw", "hello", "Content-Type:text/plain"]),
        ("redirect-stop", [url + "/redirect/302"]),
        ("redirect-follow", ["--follow", url + "/redirect/302"]),
        ("post-302", ["--follow", "POST", url + "/redirect/302", "hello=world"]),
        ("post-303", ["--follow", "POST", url + "/redirect/303", "hello=world"]),
        ("post-307", ["--follow", "POST", url + "/redirect/307", "hello=world"]),
        ("status-404", [url + "/status/404"]),
        ("status-500", [url + "/status/500"]),
        ("status-ignore", ["--no-check-status", url + "/status/404"]),
    ]
    return [{"id": identity, "args": ["--body", "--pretty=none", "--ignore-stdin", *args]} for identity, args in rows]


def protocol(requests):
    selected = {"accept", "content-type", "x-test", "user-agent"}
    return [{
        "method": request["method"],
        "path": request["path"],
        "body_b64": request["body_b64"],
        "headers": {name.lower(): value for name, value in request["headers"] if name.lower() in selected},
    } for request in requests]


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=REPOSITORY / "work/downloads/xh")
    parser.add_argument("--candidate", type=Path, default=TARGET / "implementation/target/debug/xh")
    parser.add_argument("--port", type=int, default=18463)
    parser.add_argument("--report-prefix", default="comparison")
    args = parser.parse_args()
    reference = args.reference.resolve()
    candidate = args.candidate.resolve()
    server = start(args.port)
    scenarios = cases(f"http://127.0.0.1:{server.server_port}")
    try:
        repeatability = compare.compare(reference, reference, scenarios, name="xh")
        report = compare.compare(reference, candidate, scenarios, name="xh")
        records = []
        for case in scenarios:
            pair = {"id": case["id"], "input": case}
            for label, binary in (("reference", reference), ("candidate", candidate)):
                server.requests.clear()
                output = compare.run(binary, "xh", case, 5)
                pair[label] = {"result": output, "requests": server.requests.copy()}
            pair["passed"] = protocol(pair["reference"]["requests"]) == protocol(pair["candidate"]["requests"])
            records.append(pair)
    finally:
        server.shutdown()
        server.server_close()
    prefix = TARGET / "verification/raw" / args.report_prefix
    save(prefix.with_suffix(".json"), report)
    save(prefix.parent / (prefix.name + "-repeatability.json"), repeatability)
    protocol_report = {"status": "passed" if all(record["passed"] for record in records) else "failed", "passed": sum(record["passed"] for record in records), "failed": sum(not record["passed"] for record in records), "cases": records}
    save(prefix.parent / (prefix.name + "-protocol.json"), protocol_report)
    summary = {"process": {key: report[key] for key in ("status", "passed", "failed")}, "protocol": {key: protocol_report[key] for key in ("status", "passed", "failed")}, "repeatability": repeatability["status"]}
    print(json.dumps(summary))
    for item in report["cases"]:
        if not item["passed"]:
            print(json.dumps({"id": item["input"]["id"], "differences": item["differences"], "reference": item["reference"], "candidate": item["candidate"]}))
    return 0 if report["status"] == repeatability["status"] == protocol_report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
