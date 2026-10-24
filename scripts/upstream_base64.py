#!/usr/bin/env python3
"""Export the original base64 test vectors after the source freeze."""

import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]


def export():
    project = ROOT / "evaluations/base64/target/recovered"
    if not (project / "evidence/freeze-manifest.json").is_file():
        raise ValueError("The binary-only reconstruction must freeze before the source reveal.")
    manifest = json.loads((project / "provenance.json").read_text())
    archive = ROOT / "work/downloads/coreutils-source.tar.xz"
    if not archive.exists():
        subprocess.run(["curl", "-fsSL", "--retry", "2", "--max-time", "120", manifest["source_url"], "-o", str(archive)], check=True)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["source_sha256"]:
        raise ValueError("The original source archive hash does not match.")
    directory = ROOT / "work/source-audit"
    directory.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as stream:
        member = stream.getmember(manifest["source_member_prefix"] + "tests/basenc/base64.pl")
        data = stream.extractfile(member).read()
    source = directory / "base64.pl"
    source.write_bytes(data)
    module = directory / "RustifyVectors.pm"
    module.write_text('package RustifyVectors;\nuse Exporter "import";\nuse JSON::PP;\nour @EXPORT = qw(run_tests);\nsub run_tests { my ($name,$prog,$tests)=@_; if ($prog eq "base64") { print JSON::PP->new->canonical->encode($tests); } return 0; }\n1;\n')
    raw = subprocess.check_output(["perl", "-I" + str(directory), "-MRustifyVectors", str(source)])
    vectors = json.loads(raw)
    cases = []
    expected = {}
    for vector in vectors:
        identity, *parts = vector
        args = []
        fields = {}
        for part in parts:
            if isinstance(part, str):
                args.extend(shlex.split(part))
            else:
                fields.update(part)
        if set(fields) - {"IN", "OUT", "ERR", "EXIT", "ERR_SUBST"}:
            raise ValueError("An upstream vector has unsupported fields.")
        identity = "upstream-" + identity
        error = fields.get("ERR", "").replace("base..:", "base64:")
        substitution = fields.get("ERR_SUBST")
        if substitution == "s/.*: invalid input//":
            error = "base64: invalid input\n"
        elif substitution not in (None, "s/base..:/base..:/"):
            raise ValueError("An upstream diagnostic rule needs review.")
        cases.append({"id": identity, "args": args, "stdin_b64": base64.b64encode(fields.get("IN", "").encode()).decode()})
        expected[identity] = {"returncode": fields.get("EXIT", 0), "stdout_b64": base64.b64encode(fields.get("OUT", "").encode()).decode(), "stderr_b64": base64.b64encode(error.encode()).decode()}
    result = {"source_sha256": manifest["source_sha256"], "test_file_sha256": hashlib.sha256(data).hexdigest(), "cases": cases, "expected": expected}
    (project / "upstream-vectors.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(f"The exporter recovered {len(export()['cases'])} original base64 vectors.")
