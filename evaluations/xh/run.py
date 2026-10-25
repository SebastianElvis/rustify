#!/usr/bin/env python3
"""Score an xh reconstruction against the pinned reference on a loopback HTTP fixture."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness
from cases import cases, protocol
from fixture import start
import upstream

PIN = {
    "url": "https://github.com/ducaale/xh/releases/download/v0.26.3/xh-v0.26.3-aarch64-apple-darwin.tar.gz",
    "archive_sha256": "50d61bd755942752b054297a1612ec191654f137f8939673cda83c686cb5b0f2",
    "member": "xh",
    "sha256": "ea62f476d76bdfd401e56bdee8fb2630d447aeb843b7c5fdde8bcd3de86b391d",
}


def score(reference, candidate, project):
    server = start()
    scenarios = cases(f"http://127.0.0.1:{server.server_port}")
    try:
        reports = {"repeatability": harness.compare.compare(reference, reference, scenarios, name="xh"), "process": harness.compare.compare(reference, candidate, scenarios, name="xh")}
        records = []
        for case in scenarios:
            pair = {"id": case["id"], "input": case}
            for label, binary in (("reference", reference), ("candidate", candidate)):
                server.requests.clear()
                pair[label] = {"result": harness.compare.run(binary, "xh", case, 5), "requests": server.requests.copy()}
            pair["passed"] = protocol(pair["reference"]["requests"]) == protocol(pair["candidate"]["requests"])
            records.append(pair)
    finally:
        server.shutdown()
        server.server_close()
    reports["protocol"] = {"status": "passed" if all(record["passed"] for record in records) else "failed", "passed": sum(record["passed"] for record in records), "failed": sum(not record["passed"] for record in records), "cases": records}
    reports["upstream"] = upstream.evaluate(reference, candidate)
    return reports, []


if __name__ == "__main__":
    raise SystemExit(harness.run("xh", PIN, score))
