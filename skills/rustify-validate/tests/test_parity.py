import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/parity.py"
SPEC = importlib.util.spec_from_file_location("parity", SCRIPT)
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


class ParityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.write("implementation/main.rs", "fn main() {}\n")
        self.write("recovered/evidence/original.json", {"returncode": 0})
        self.evidence = [{"id": "E1", "classification": "observed"}]
        self.tests = [{"id": "T1", "origin": "observed", "evidence": ["E1"], "scenarios": ["S1"], "expect": {"returncode": 0, "stdout_b64": "YQ=="}}]
        result = {"returncode": 0, "stdout_b64": "YQ==", "stderr_b64": "", "error": None}
        self.report = {"status": "passed", "passed": 1, "failed": 0, "executables": {"reference": {"sha256": "a" * 64}}, "cases": [{"input": {"id": "S1"}, "reference": result.copy(), "candidate": result.copy(), "passed": True, "differences": []}]}
        self.matrix = {
            "target_sha256": "a" * 64, "surface_complete": True, "scope": "full_product", "selected_features": ["F1"],
            "original_features": [{"id": "F1", "classification": "observed", "evidence": ["E1"]}],
            "mappings": [{"feature": "F1", "evidence": ["E1"], "rust": ["implementation/main.rs"], "tests": ["T1"], "dimensions": {name: "matched" for name in parity.DIMENSIONS}}],
            "evidence_files": [{"id": "E1", "path": "recovered/evidence/original.json", "sha256": self.sha("recovered/evidence/original.json")}],
            "comparison": {"path": "verification/comparison.json", "sha256": ""},
        }

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value))

    def sha(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def run_check(self, partial=False):
        self.write("recovered/evidence.json", self.evidence)
        self.write("recovered/tests.json", self.tests)
        self.write("verification/comparison.json", self.report)
        self.matrix["comparison"]["sha256"] = self.sha("verification/comparison.json")
        self.write("verification/parity-matrix.json", self.matrix)
        return parity.check(self.root, allow_partial=partial)

    def test_complete_declared_records_pass_only_the_evidence_gate(self):
        result = self.run_check()
        self.assertEqual(result["assessment"], "full_parity_gate_pass")
        self.assertEqual(result["status"], "passed")
        self.assertIs(result["full_parity_gate_pass"], True)
        self.assertIs(result["semantic_truth_verified"], False)
        self.assertEqual(result["inputs"]["implementation/main.rs"], self.sha("implementation/main.rs"))

    def test_unmapped_original_feature_blocks_full_completion(self):
        self.matrix["original_features"].append({"id": "F2", "classification": "observed", "evidence": ["E1"]})
        self.assertEqual(self.run_check()["status"], "failed")
        result = self.run_check(True)
        self.assertEqual(result["status"], "partial")
        self.assertIs(result["full_parity_gate_pass"], False)
        self.assertNotEqual(result["assessment"], "full_parity_gate_pass")
        self.assertTrue(any("no Rust mapping" in gap for gap in result["gaps"]))

    def test_every_nonmatching_dimension_blocks_full_completion(self):
        for status in ("different", "unknown", "unmapped", "untested", "user_exception"):
            with self.subTest(status=status):
                self.matrix["mappings"][0]["dimensions"]["ux"] = status
                self.assertEqual(self.run_check()["status"], "failed")

    def test_unknown_inventory_and_inferred_claims_remain_gaps(self):
        self.matrix["surface_complete"] = False
        self.matrix["original_features"][0]["classification"] = "inferred"
        self.evidence[0]["classification"] = "unknown"
        result = self.run_check()
        self.assertEqual(result["status"], "failed")
        self.assertGreaterEqual(len(result["gaps"]), 3)

    def test_missing_evidence_or_test_links_fail_even_in_partial_mode(self):
        self.matrix["mappings"][0]["tests"] = ["missing"]
        self.assertTrue(self.run_check(True)["errors"])
        self.matrix["mappings"][0]["tests"] = ["T1"]
        self.matrix["mappings"][0]["evidence"] = ["missing"]
        self.assertTrue(self.run_check(True)["errors"])

    def test_matching_wrong_outputs_fail_independent_expectations(self):
        for label in ("reference", "candidate"):
            self.report["cases"][0][label]["returncode"] = 1
        result = self.run_check()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(sum("exact expected" in gap for gap in result["gaps"]), 2)

    def test_missing_exact_expectations_cannot_pass_from_labels(self):
        self.tests[0]["expect"] = {}
        self.assertTrue(self.run_check()["errors"])

    def test_proposed_case_keeps_its_origin_without_granting_product_changes(self):
        self.tests[0]["origin"] = "proposed"
        self.assertEqual(self.run_check()["status"], "passed")
        self.matrix["mappings"][0]["dimensions"]["product"] = "different"
        self.assertEqual(self.run_check()["status"], "failed")

    def test_duplicate_features_and_inconsistent_case_totals_fail(self):
        self.matrix["original_features"].append(copy.deepcopy(self.matrix["original_features"][0]))
        self.assertTrue(self.run_check()["errors"])
        self.matrix["original_features"].pop()
        self.report["passed"] = 2
        self.assertTrue(self.run_check()["errors"])

    def test_changed_evidence_and_path_escape_fail(self):
        self.write("recovered/evidence/original.json", {"returncode": 1})
        self.assertTrue(self.run_check(True)["errors"])
        self.matrix["evidence_files"][0]["path"] = "../outside.json"
        self.assertTrue(self.run_check(True)["errors"])

    def test_boolean_values_do_not_match_numeric_expectations(self):
        self.report["cases"][0]["candidate"]["returncode"] = False
        self.assertEqual(self.run_check()["status"], "failed")

    def test_invalid_original_identity_cannot_pass(self):
        self.matrix["target_sha256"] = "unknown"
        self.report["executables"]["reference"]["sha256"] = "unknown"
        self.assertTrue(self.run_check(True)["errors"])

    def test_operational_state_and_gate_output_cannot_be_inputs(self):
        for name in ("recovered/state.json", "verification/parity.json"):
            with self.subTest(name=name):
                self.write(name, {"state": "operational"})
                self.matrix["evidence_files"][0].update(path=name, sha256=self.sha(name))
                self.assertTrue(self.run_check(True)["errors"])

    def test_unexecuted_cases_remain_gaps_in_partial_mode(self):
        self.tests[0]["scenarios"] = ["unexecuted"]
        self.assertEqual(self.run_check()["status"], "failed")
        result = self.run_check(True)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(any("no executed capture" in gap for gap in result["gaps"]))

    def test_copyable_matrix_stays_incomplete_until_verified(self):
        text = (SCRIPT.parents[1] / "assets/parity-matrix.json").read_text()
        values = {"TARGET_SHA256": "a" * 64, "FEATURE_ID": "F1", "EVIDENCE_ID": "E1", "RUST_FILE": "main.rs", "TEST_ID": "T1", "CAPTURE_FILE": "original.json", "CAPTURE_SHA256": self.sha("recovered/evidence/original.json"), "COMPARISON_SHA256": "0" * 64}
        for name, value in values.items():
            text = text.replace("{{" + name + "}}", value)
        self.matrix = json.loads(text)
        self.write("implementation/src/main.rs", "fn main() {}\n")
        result = self.run_check()
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["errors"])
        self.matrix["surface_complete"] = True
        self.matrix["original_features"][0]["classification"] = "observed"
        self.matrix["mappings"][0]["dimensions"] = {name: "matched" for name in parity.DIMENSIONS}
        self.assertEqual(self.run_check()["status"], "passed")

    def test_input_manifest_includes_opaque_implementation_assets(self):
        self.write("implementation/layout.dat", "original layout")
        result = self.run_check()
        self.assertEqual(result["inputs"]["implementation/layout.dat"], self.sha("implementation/layout.dat"))
        self.write("implementation/layout.dat", "changed layout")
        self.assertNotEqual(result["inputs"]["implementation/layout.dat"], self.sha("implementation/layout.dat"))

    def test_cli_partial_mode_returns_gaps_without_a_full_pass(self):
        self.matrix["surface_complete"] = False
        self.run_check()
        report = self.root / "verification/parity.json"
        command = [sys.executable, str(SCRIPT), "--project", str(self.root), "--report", str(report)]
        result = subprocess.run(command, capture_output=True)
        self.assertEqual(result.returncode, 1)
        result = subprocess.run(command + ["--allow-partial"], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(report.read_text())["status"], "partial")


if __name__ == "__main__":
    unittest.main()
