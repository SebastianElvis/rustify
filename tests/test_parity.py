import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/rustify-validate/scripts/parity.py"
SPEC = importlib.util.spec_from_file_location("parity", SCRIPT)
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


class ParityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.write("implementation/src/main.rs", "mod codec;\nfn main() { codec::run(); }\n")
        self.write("implementation/src/codec.rs", "pub fn run() {}\n")
        self.write("recovered/evidence/original.json", {"returncode": 0})
        self.write("recovered/product.md", "REQ-1\n")
        self.write("recovered/ux.md", "No visual surface.\n")
        self.write("recovered/architecture.md", "C-1 C-2\n")
        self.write("implementation/docs/design.md", "C-1 C-2\n")
        self.write("recovered/roadmap.md", "No open gaps.\n")
        self.contract = {"target": {"sha256": "a" * 64}, "scope": {"mode": "full_product", "user_instruction": None}}
        self.evidence = [{"id": "E1", "classification": "observed", "path": "recovered/evidence/original.json", "sha256": self.sha("recovered/evidence/original.json")}]
        self.tests = [{"id": "T1", "origin": "observed", "evidence": ["E1"], "scenarios": ["S1"], "expect": {"returncode": 0, "stdout_b64": "YQ=="}}]
        result = {"returncode": 0, "stdout_b64": "YQ==", "stderr_b64": "", "error": None}
        self.report = {"status": "passed", "passed": 1, "failed": 0, "executables": {"reference": {"sha256": "a" * 64}}, "cases": [{"input": {"id": "S1"}, "reference": result.copy(), "candidate": result.copy(), "passed": True, "differences": []}]}
        self.model = {
            "inventory": {"complete": True, "basis": ["E1"]},
            "requirements": [{
                "id": "REQ-1", "dimension": "behavior", "pattern": "event",
                "statement": "When the user supplies input, the demo shall write the encoded result.",
                "classification": "observed", "evidence": ["E1"], "verification": "test", "tests": ["T1"], "records": [], "components": ["C-1", "C-2"],
            }],
            "components": [
                {"id": "C-1", "name": "Entry", "level": "component", "responsibility": "Parse input.", "classification": "observed", "evidence": ["E1"]},
                {"id": "C-2", "name": "Codec", "level": "component", "responsibility": "Encode bytes.", "classification": "observed", "evidence": ["E1"]},
            ],
            "edges": [{"id": "EDGE-1", "source": "C-1", "target": "C-2", "kind": "control", "classification": "observed", "evidence": ["E1"]}],
            "correspondences": [{"original": "C-1", "rust": "implementation/src/main.rs"}, {"original": "C-2", "rust": "implementation/src/codec.rs"}],
            "slices": [{"id": "SLICE-1", "kind": "skeleton", "requirements": ["REQ-1"], "depends_on": [], "risk": "high"}],
            "exceptions": [], "gaps": [],
        }

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value))

    def sha(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def run_check(self, partial=False):
        for name, value in (("recovered/contract.json", self.contract), ("recovered/model.json", self.model), ("recovered/evidence.json", self.evidence), ("recovered/tests.json", self.tests), ("verification/comparison.json", self.report)):
            self.write(name, value)
        return parity.check(self.root, allow_partial=partial)

    def test_complete_records_pass_only_the_evidence_gate(self):
        result = self.run_check()
        self.assertEqual(result["assessment"], "full_parity_pass")
        self.assertEqual(result["status"], "passed")
        self.assertIs(result["semantic_truth_verified"], False)
        self.assertEqual(result["reflexion"]["convergences"], ["EDGE-1"])
        self.assertEqual(result["slices"], {"SLICE-1": True})
        self.assertEqual(result["inputs"]["implementation/src/main.rs"], self.sha("implementation/src/main.rs"))

    def test_statements_must_follow_one_ears_pattern(self):
        for statement in ("The demo encodes input.", "When the user supplies input, the demo shall encode it and shall wrap it.", "the demo shall encode input.", "When {{TRIGGER}}, the demo shall respond."):
            with self.subTest(statement=statement):
                self.model["requirements"][0]["statement"] = statement
                self.assertTrue(self.run_check(True)["errors"])
        self.model["requirements"][0].update(pattern="unwanted", statement="If the input is invalid, then the demo shall exit with status 1.")
        self.assertEqual(self.run_check()["status"], "passed")

    def test_reflexion_reports_absence_merge_divergence_and_extra_modules(self):
        self.write("implementation/src/main.rs", "mod codec;\nfn main() {}\n")
        self.assertIn("EDGE-1: The reflexion check reports absences.", self.run_check()["gaps"])
        self.write("implementation/src/main.rs", "mod codec;\nfn main() { codec::run(); }\n")
        self.write("implementation/src/codec.rs", "pub fn run() { util::help(); }\n")
        self.write("implementation/src/util.rs", "pub fn help() {}\n")
        self.model["components"].append({"id": "C-3", "name": "Util", "level": "component", "responsibility": "Help.", "classification": "observed", "evidence": ["E1"]})
        self.model["correspondences"].append({"original": "C-3", "rust": "implementation/src/util.rs"})
        self.write("recovered/architecture.md", "C-1 C-2 C-3\n")
        self.write("implementation/docs/design.md", "C-1 C-2 C-3\n")
        result = self.run_check()
        self.assertEqual(result["reflexion"]["divergences"], ["implementation/src/codec.rs -> implementation/src/util.rs"])
        self.model["correspondences"][2]["rust"] = "implementation/src/codec.rs"
        result = self.run_check()
        self.assertEqual(result["reflexion"]["merged"], ["implementation/src/codec.rs"])
        self.assertEqual(result["reflexion"]["extra_modules"], ["implementation/src/util.rs"])
        self.model["correspondences"].pop()
        self.assertEqual(self.run_check()["reflexion"]["unmapped"], ["C-3"])

    def test_exceptions_permit_a_scoped_pass_but_never_a_full_pass(self):
        self.write("implementation/src/extra.rs", "pub fn extra() {}\n")
        self.model["exceptions"] = [{"id": "EXC-1", "items": ["implementation/src/extra.rs"], "user_instruction": "Keep the helper module.", "limit": "One helper."}]
        result = self.run_check()
        self.assertEqual(result["exceptions_used"], ["implementation/src/extra.rs"])
        self.assertEqual(result["assessment"], "incomplete")
        self.contract["scope"].update(mode="subset", user_instruction="Evaluate REQ-1 only.")
        self.assertEqual(self.run_check()["assessment"], "scoped_pass")
        self.model["exceptions"][0]["user_instruction"] = None
        self.assertEqual(self.run_check()["assessment"], "incomplete")

    def test_subset_needs_a_user_instruction_and_keeps_full_gaps_visible(self):
        self.model["requirements"].append({**copy.deepcopy(self.model["requirements"][0]), "id": "REQ-2", "in_scope": False, "tests": [], "classification": "unknown"})
        self.write("recovered/product.md", "REQ-1 REQ-2\n")
        self.contract["scope"]["mode"] = "subset"
        self.assertEqual(self.run_check()["assessment"], "incomplete")
        self.contract["scope"]["user_instruction"] = "Evaluate REQ-1 only."
        result = self.run_check()
        self.assertEqual(result["assessment"], "scoped_pass")
        self.assertTrue(any(gap.startswith("REQ-2:") for gap in result["gaps"]))
        self.contract["scope"]["mode"] = "full_product"
        self.assertIn("The full-product contract cannot exclude a requirement.", self.run_check()["gaps"])

    def test_uncertain_inventory_and_claims_remain_gaps(self):
        self.model["inventory"]["complete"] = False
        self.model["requirements"][0]["classification"] = "inferred"
        self.evidence[0] = {"id": "E1", "classification": "unknown"}
        result = self.run_check()
        self.assertEqual(result["assessment"], "incomplete")
        self.assertGreaterEqual(len(result["gaps"]), 4)

    def test_matching_wrong_outputs_fail_independent_expectations(self):
        for label in ("reference", "candidate"):
            self.report["cases"][0][label]["returncode"] = 1
        result = self.run_check()
        self.assertEqual(result["assessment"], "failed")
        self.assertEqual(sum("exact expected" in gap for gap in result["gaps"]), 2)

    def test_recorded_difference_fails_the_requirement(self):
        self.report["cases"][0].update(passed=False, differences=["stdout_b64"])
        self.report.update(status="failed", passed=0, failed=1)
        self.assertEqual(self.run_check()["requirements"], {"REQ-1": "failed"})

    def test_open_gaps_block_and_must_appear_in_the_roadmap(self):
        self.model["gaps"] = [{"id": "GAP-1", "items": ["REQ-1"], "kind": "difference", "status": "open"}]
        result = self.run_check()
        self.assertIn("REQ-1: The gap GAP-1 remains open.", result["gaps"])
        self.assertIn("GAP-1: recovered/roadmap.md does not name this open gap.", result["gaps"])
        self.model["gaps"][0]["status"] = "closed"
        self.assertEqual(self.run_check()["status"], "passed")

    def test_documents_must_name_every_requirement_and_component(self):
        self.write("recovered/architecture.md", "C-1\n")
        self.assertIn("C-2: recovered/architecture.md does not name this item.", self.run_check()["gaps"])
        self.write("recovered/architecture.md", "C-1 C-2\n")
        self.write("recovered/product.md", "REQ-10\n")
        self.assertEqual(self.run_check()["assessment"], "incomplete")

    def test_non_test_methods_need_bound_records(self):
        self.model["requirements"][0].update(verification="inspection", tests=[])
        self.assertEqual(self.run_check()["assessment"], "incomplete")
        self.model["requirements"][0]["records"] = ["E1"]
        self.assertEqual(self.run_check()["assessment"], "full_parity_pass")

    def test_missing_links_and_invalid_records_fail_even_in_partial_mode(self):
        for change in (
            lambda: self.model["requirements"][0].update(tests=["missing"]),
            lambda: self.model["requirements"][0].update(evidence=["missing"]),
            lambda: self.model["requirements"][0].update(components=["C-9"]),
            lambda: self.model["requirements"][0].update(dimension="components"),
            lambda: self.model["edges"][0].update(target="C-9"),
            lambda: self.model["correspondences"].append({"original": "C-1", "rust": "implementation/src/codec.rs"}),
            lambda: self.model["correspondences"][0].update(rust="implementation/src/missing.rs"),
            lambda: self.tests[0].update(expect={}),
            lambda: self.report.update(passed=2),
            lambda: self.contract["target"].update(sha256="unknown"),
        ):
            with self.subTest(change=change):
                saved = copy.deepcopy((self.model, self.tests, self.report, self.contract))
                change()
                self.assertTrue(self.run_check(True)["errors"])
                self.model, self.tests, self.report, self.contract = saved

    def test_changed_evidence_and_path_escape_fail(self):
        self.write("recovered/evidence/original.json", {"returncode": 1})
        self.assertTrue(self.run_check(True)["errors"])
        self.evidence[0]["path"] = "../outside.json"
        self.assertTrue(self.run_check(True)["errors"])

    def test_operational_state_and_gate_output_cannot_be_inputs(self):
        for name in ("recovered/state.json", "verification/parity.json"):
            with self.subTest(name=name):
                self.write(name, {"state": "operational"})
                self.evidence[0].update(path=name, sha256=self.sha(name))
                self.assertTrue(self.run_check(True)["errors"])

    def test_unexecuted_cases_remain_gaps_in_partial_mode(self):
        self.tests[0]["scenarios"] = ["unexecuted"]
        result = self.run_check(True)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(any("no executed capture" in gap for gap in result["gaps"]))

    def test_copyable_ledger_stays_incomplete_until_verified(self):
        text = (SCRIPT.parents[2] / "rustify/assets/model.json").read_text()
        for name, value in {"INVENTORY_EVIDENCE_ID": "E1", "TRIGGER": "the user supplies input", "SYSTEM": "demo", "RESPONSE": "write the encoded result", "EVIDENCE_ID": "E1", "TEST_ID": "T1", "COMPONENT_NAME": "Entry", "RESPONSIBILITY": "Parse input.", "CLOSURE_CHECK": "T1"}.items():
            text = text.replace("{{" + name + "}}", value)
        self.model = json.loads(text)
        self.write("recovered/product.md", "REQ-001\n")
        self.write("recovered/architecture.md", "C-001\n")
        self.write("implementation/docs/design.md", "C-001\n")
        self.write("recovered/roadmap.md", "GAP-001\n")
        self.write("implementation/src/codec.rs", "")
        (self.root / "implementation/src/codec.rs").unlink()
        result = self.run_check()
        self.assertEqual(result["assessment"], "incomplete")
        self.assertFalse(result["errors"])

    def test_input_manifest_includes_opaque_implementation_assets(self):
        self.write("implementation/layout.dat", "original layout")
        self.write("implementation/target/ignored", "build output")
        result = self.run_check()
        self.assertEqual(result["inputs"]["implementation/layout.dat"], self.sha("implementation/layout.dat"))
        self.assertNotIn("implementation/target/ignored", result["inputs"])

    def test_cli_partial_mode_returns_gaps_without_a_full_pass(self):
        self.model["inventory"]["complete"] = False
        self.run_check()
        report = self.root / "verification/parity.json"
        command = [sys.executable, str(SCRIPT), "--project", str(self.root), "--report", str(report)]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
        self.assertEqual(subprocess.run(command + ["--allow-partial"], capture_output=True).returncode, 0)
        self.assertEqual(json.loads(report.read_text())["status"], "partial")


if __name__ == "__main__":
    unittest.main()
