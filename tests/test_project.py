import hashlib
import importlib.util
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

import yaml


SPEC = importlib.util.spec_from_file_location("project", Path(__file__).parents[1] / "skills/rustify/scripts/project.py")
project = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(project)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name).resolve()
        self.root = self.base / "target"
        self.target = self.base / "original"
        self.target.write_bytes(b"original binary")
        self.workspace = Path(project.init(self.root, self.target, "cli")["work_dir"])

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)

    def model(self, **changes):
        model = {
            "inventory": {"complete": True}, "surface": [],
            "requirements": [{"id": "REQ-1", "components": ["C-1"]}],
            "components": [{"id": "C-1"}], "edges": [],
            "correspondences": [{"original": "C-1", "rust": "implementation/src/main.rs"}],
            "slices": [{"id": "S-1", "kind": "skeleton", "requirements": ["REQ-1"], "depends_on": [], "risk": "high"}],
            "gaps": [],
        }
        self.write("recovered/model.yaml", yaml.safe_dump({**model, **changes}))

    def checks(self, returncode=0):
        records = []
        for name in ("fmt", "clippy", "test"):
            self.write(f"verification/logs/{name}.log", "log\n")
            records.append({"name": name, "returncode": returncode, "log": f"verification/logs/{name}.log", "log_sha256": project.digest(self.root / f"verification/logs/{name}.log")})
        self.write("verification/checks.yaml", yaml.safe_dump({"status": "passed", "inputs_sha256": project.combined(project.tree(self.root, "implementation")), "commands": records}))

    def artifacts(self, phase):
        for name in project.REQUIRED[phase]:
            name = name.partition("#")[0]
            if name == "recovered/model.yaml":
                self.model()
            elif name != "verification/parity.yaml":
                self.write(name, yaml.safe_dump({"content": True}) if name.endswith(".yaml") else "content\n")
        if phase == "implement":
            self.write("implementation/src/main.rs", "fn main() {}\n")
            self.checks()
        if phase == "validate":
            self.write("implementation/target/release/base64", "candidate binary")
            candidate = self.root / "implementation/target/release/base64"
            self.write("verification/comparison.yaml", yaml.safe_dump({
                "status": "passed", "passed": 1, "failed": 0,
                "cases": [{"passed": True, "differences": []}],
                "executables": {
                    "reference": {"path": str(self.target), "sha256": project.digest(self.target)},
                    "candidate": {"path": str(candidate), "sha256": project.digest(candidate)},
                },
            }))
            self.parity()

    def parity(self, **changes):
        valid = {"assessment": "full_parity_pass", "errors": [], "gaps": [], "target_sha256": project.digest(self.target), "inputs": {name: project.digest(self.root / name) for name in ("recovered/product.md", "recovered/model.yaml")}}
        self.write("verification/parity.yaml", yaml.safe_dump({**valid, **changes}))

    def through(self, last):
        for phase in project.PHASES:
            self.artifacts(phase)
            project.checkpoint(self.root, phase)
            if phase == last:
                break

    def test_restart_and_ordered_checkpoints(self):
        self.assertEqual(project.status(self.root)["next"], "discover")
        with self.assertRaises(ValueError):
            project.checkpoint(self.root, "plan")
        with self.assertRaises(ValueError):
            project.init(self.root, self.target, "cli")
        self.through("validate")
        self.assertEqual(project.status(str(self.root)), {"completed": list(project.PHASES), "next": None, "stale": None})

    def test_missing_empty_and_invalid_artifacts_fail(self):
        self.artifacts("discover")
        (self.root / "recovered/evidence.yaml").unlink()
        for data in (None, "", "  \n", "{}", "[]", "invalid", "null", "invalid: [yaml"):
            with self.subTest(data=data):
                if data is not None:
                    self.write("recovered/evidence.yaml", data)
                with self.assertRaises((ValueError, OSError, yaml.YAMLError)):
                    project.checkpoint(self.root, "discover")
        self.assertEqual(project.status(self.root)["next"], "discover")

    def test_target_change_requires_new_project(self):
        self.target.write_bytes(b"different target")
        with self.assertRaisesRegex(ValueError, "new project"):
            project.status(self.root)
        with self.assertRaisesRegex(ValueError, "new project"):
            project.checkpoint(self.root, "discover")

    def test_stale_artifact_invalidates_later_phases(self):
        self.through("validate")
        self.write("recovered/product.md", "The new evidence changes this product.\n")
        self.assertEqual(project.status(self.root), {"completed": [], "next": "discover", "stale": "discover"})
        with self.assertRaises(ValueError):
            project.checkpoint(self.root, "validate")
        project.checkpoint(self.root, "discover")
        self.assertEqual(project.status(self.root)["next"], "plan")
        state = yaml.safe_load((self.root / "recovered/state.yaml").read_text())
        self.assertEqual(list(state["checkpoints"]), ["discover"])

    def test_missing_artifact_reopens_phase(self):
        self.through("plan")
        (self.root / "recovered/ux.md").unlink()
        self.assertEqual(project.status(self.root)["stale"], "discover")

    def test_source_changes_and_additions_reopen_implementation(self):
        self.through("validate")
        self.write("implementation/src/main.rs", "fn main() { println!(\"change\"); }\n")
        self.assertEqual(project.status(self.root)["stale"], "implement")
        self.checks()
        project.checkpoint(self.root, "implement")
        self.write("implementation/src/new.rs", "pub fn new() {}\n")
        self.assertEqual(project.status(self.root)["stale"], "implement")

    def test_all_implementation_inputs_reopen_implementation(self):
        self.through("validate")
        for name, content in (
            ("src/help.txt", "changed help"), ("src/version.txt", "changed version"),
            ("tests/empty.bin", ""), ("tests/malformed.yaml", "invalid: [yaml"),
            (".cargo/config.toml", '[build]\nrustflags = []\n'),
        ):
            with self.subTest(name=name):
                self.write("implementation/" + name, content)
                self.assertEqual(project.status(self.root)["stale"], "implement")
                self.checks()
                project.checkpoint(self.root, "implement")
                path = self.root / "implementation" / name
                path.write_text(content + "changed")
                self.assertEqual(project.status(self.root)["stale"], "implement")
                self.checks()
                project.checkpoint(self.root, "implement")
                path.unlink()
                self.assertEqual(project.status(self.root)["stale"], "implement")
                self.checks()
                project.checkpoint(self.root, "implement")
        self.write("implementation/target/build-output", "ignored")
        self.write("implementation/.git/index", "ignored")
        self.assertIsNone(project.status(self.root)["stale"])
        link = self.root / "implementation/src/linked.txt"
        link.symlink_to(self.target)
        self.assertEqual(project.status(self.root)["stale"], "implement")
        with self.assertRaisesRegex(ValueError, "symlink"):
            project.checkpoint(self.root, "implement")

    def test_required_checks_bind_to_the_current_implementation(self):
        self.through("plan")
        self.artifacts("implement")
        path = self.root / "verification/checks.yaml"
        valid = yaml.safe_load(path.read_text())
        for invalid in (
            {**valid, "status": "failed"},
            {**valid, "commands": valid["commands"][:-1]},
            {**valid, "inputs_sha256": "stale"},
            {**valid, "commands": valid["commands"] + [{**valid["commands"][-1], "returncode": 101}]},
            {**valid, "commands": valid["commands"][:-1] + [{**valid["commands"][-1], "log_sha256": "forged"}]},
        ):
            with self.subTest(invalid=invalid):
                path.write_text(yaml.safe_dump(invalid))
                with self.assertRaises(ValueError):
                    project.checkpoint(self.root, "implement")
        self.checks()
        project.checkpoint(self.root, "implement")
        self.write("implementation/src/main.rs", "fn main() { println!(); }\n")
        with self.assertRaisesRegex(ValueError, "current implementation"):
            project.checkpoint(self.root, "implement")

    def test_check_command_runs_cargo_and_records_mutation_score(self):
        self.through("plan")
        self.artifacts("implement")
        tools = self.base / "tools"
        tools.mkdir()
        cargo = tools / "cargo"
        cargo.write_text("#!/bin/sh\n"
            "if [ \"$1\" = mutants ]; then mkdir -p \"$3/mutants.out\"; echo '{\"caught\": 3, \"missed\": 1, \"timeout\": 0, \"unviable\": 2}' > \"$3/mutants.out/outcomes.json\"; exit 2; fi\n"
            "echo \"ran $1\"; exit ${FAKE_STATUS:-0}\n")
        cargo.chmod(0o755)
        environment = {"PATH": f"{tools}:{os.environ['PATH']}"}
        with patch.dict(os.environ, environment):
            result = project.check(self.root, ["mutants"])
        self.assertEqual(result["status"], "passed")
        checks = yaml.safe_load((self.root / "verification/checks.yaml").read_text())
        self.assertEqual(checks["commands"][-1]["mutation"], {"caught": 3, "missed": 1, "timeout": 0, "unviable": 2, "score": 0.75})
        project.checkpoint(self.root, "implement")
        with patch.dict(os.environ, {**environment, "FAKE_STATUS": "1"}):
            self.assertEqual(project.check(self.root)["status"], "failed")
        self.assertEqual(project.status(self.root)["stale"], "implement")

    def test_resource_limit_blocks_a_check_with_zero_exit_status(self):
        self.through("plan")
        self.artifacts("implement")
        completed = type("Completed", (), {"returncode": 0, "stdout": b"", "stderr": b""})()
        with patch.object(project.supervisor, "execute", return_value=(completed, "The process group exceeded the memory limit.", {})), patch("sys.argv", ["project.py", "check", str(self.root), "--mutants"]):
            self.assertEqual(project.main(), 1)
        checks = yaml.safe_load((self.root / "verification/checks.yaml").read_text())
        self.assertTrue(checks["status"] == "failed" and all(record["returncode"] == 1 and record["error"] for record in checks["commands"][-4:]))

    def test_plan_needs_one_skeleton_an_acyclic_graph_and_full_coverage(self):
        self.through("discover")
        self.artifacts("plan")
        skeleton = {"id": "S-1", "kind": "skeleton", "requirements": ["REQ-1"], "depends_on": [], "risk": "high"}
        for slices in (
            [],
            [{**skeleton, "kind": "slice"}],
            [skeleton, {**skeleton, "id": "S-2"}],
            [skeleton, {"id": "S-2", "kind": "slice", "requirements": ["REQ-1"], "depends_on": [], "risk": "low"}],
            [skeleton, {"id": "S-2", "kind": "slice", "requirements": ["REQ-1"], "depends_on": ["S-3"], "risk": "low"}, {"id": "S-3", "kind": "slice", "requirements": ["REQ-1"], "depends_on": ["S-2"], "risk": "low"}],
            [{**skeleton, "requirements": ["REQ-2"]}],
            [{**skeleton, "risk": "unknown"}],
        ):
            with self.subTest(slices=slices):
                self.model(slices=slices)
                with self.assertRaises((ValueError, KeyError)):
                    project.checkpoint(self.root, "plan")
        self.model(requirements=[{"id": "REQ-1", "components": ["C-1"]}, {"id": "REQ-2", "components": ["C-1"]}])
        project.checkpoint(self.root, "discover")
        with self.assertRaisesRegex(ValueError, "Every requirement"):
            project.checkpoint(self.root, "plan")
        self.model(correspondences=[{"original": "C-9", "rust": "implementation/src/main.rs"}])
        project.checkpoint(self.root, "discover")
        with self.assertRaisesRegex(ValueError, "unknown original"):
            project.checkpoint(self.root, "plan")
        self.model()
        project.checkpoint(self.root, "plan")

    def test_ledger_sections_reopen_only_their_owning_phase(self):
        self.through("validate")
        for changes, phase in (
            ({"gaps": [{"id": "GAP-1", "items": ["REQ-1"], "kind": "difference", "status": "open"}]}, "validate"),
            ({"slices": [{"id": "S-1", "kind": "skeleton", "requirements": ["REQ-1"], "depends_on": [], "risk": "low"}]}, "plan"),
            ({"requirements": [{"id": "REQ-1", "components": ["C-1"], "statement": "changed"}]}, "discover"), ({"surface": [{"id": "SURF-1", "requirements": []}]}, "discover"),
        ):
            self.model(**changes)
            self.assertEqual(project.status(self.root)["stale"], phase)
        self.write("recovered/model.yaml", yaml.safe_dump({"requirements": []}))
        with self.assertRaisesRegex(ValueError, "section"):
            project.checkpoint(self.root, "discover")

    def test_failed_or_empty_comparison_cannot_complete(self):
        self.through("implement")
        self.artifacts("validate")
        path = self.root / "verification/comparison.yaml"
        original = yaml.safe_load(path.read_text())
        for changes in (
            {"status": "failed"}, {"failed": 1}, {"passed": 0},
            {"cases": []}, {"passed": 2}, {"cases": [{"passed": False, "differences": []}]},
            {"cases": [{"passed": True, "differences": ["stdout_b64"]}]},
        ):
            path.write_text(yaml.safe_dump({**original, **changes}))
            with self.assertRaises(ValueError):
                project.checkpoint(self.root, "validate")
        self.assertEqual(project.status(self.root)["next"], "validate")

    def test_wrong_target_or_changed_candidate_cannot_complete(self):
        self.through("implement")
        self.artifacts("validate")
        path = self.root / "verification/comparison.yaml"
        report = yaml.safe_load(path.read_text())
        report["executables"]["reference"]["sha256"] = "bad"
        path.write_text(yaml.safe_dump(report))
        with self.assertRaisesRegex(ValueError, "different target"):
            project.checkpoint(self.root, "validate")
        self.artifacts("validate")
        project.checkpoint(self.root, "validate")
        self.write("implementation/target/release/base64", "changed candidate")
        self.assertEqual(project.status(self.root)["stale"], "validate")
        with self.assertRaisesRegex(ValueError, "candidate changed"):
            project.checkpoint(self.root, "validate")

    def test_symlinks_and_external_artifacts_fail(self):
        self.artifacts("discover")
        (self.root / "recovered/evidence.yaml").unlink()
        (self.base / "outside").write_text("content: true\n")
        (self.root / "recovered/evidence.yaml").symlink_to(self.base / "outside")
        with self.assertRaisesRegex(ValueError, "symlink"):
            project.checkpoint(self.root, "discover")
        with self.assertRaisesRegex(ValueError, "inside"):
            project.artifact(self.root, "../outside")
        with self.assertRaisesRegex(ValueError, "inside"):
            project.artifact(self.root, "/outside")

    def test_state_hashes_match_actual_artifacts(self):
        self.through("discover")
        state = yaml.safe_load((self.root / "recovered/state.yaml").read_text())
        expected = hashlib.sha256((self.root / "recovered/evidence.yaml").read_bytes()).hexdigest()
        self.assertEqual(state["checkpoints"]["discover"]["recovered/evidence.yaml"], expected)

    def test_workspace_stays_outside_the_three_project_directories(self):
        self.assertEqual({p.name for p in self.root.iterdir()}, {"recovered", "implementation", "verification"})
        self.assertEqual(self.workspace, self.base / ".target-rustify")
        self.assertTrue((self.root / "recovered/state.yaml").is_file())
        self.through("plan")
        self.assertTrue((self.root / "implementation/docs/design.md").is_file())
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_custom_workspace_and_separation_guards(self):
        other = self.base / "other"
        custom = self.base / "agent"
        state = project.init(other, self.target, "cli", custom)
        self.assertEqual(state["work_dir"], str(custom))
        self.assertEqual(state["version"], 3)
        for workspace in (self.base / "unused", self.base / "unused/agent"):
            with self.subTest(workspace=workspace), self.assertRaisesRegex(ValueError, "outside"):
                project.init(self.base / "unused", self.target, "cli", workspace)
        link = self.base / "agent-link"
        link.symlink_to(custom, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            project.init(self.base / "unused", self.target, "cli", link)

    def test_plan_edits_reopen_planning(self):
        self.through("validate")
        self.write("implementation/docs/design.md", "The design changes.\n")
        self.assertEqual(project.status(self.root), {"completed": ["discover"], "next": "plan", "stale": "plan"})
        with self.assertRaises(ValueError):
            project.checkpoint(self.root, "implement")

    def test_raw_evidence_edits_and_deletions_reopen_discovery(self):
        self.write("recovered/evidence/stdout.bin", "")
        self.through("validate")
        self.write("recovered/evidence/stdout.bin", "new capture")
        self.assertEqual(project.status(self.root)["stale"], "discover")
        project.checkpoint(self.root, "discover")
        (self.root / "recovered/evidence/stdout.bin").unlink()
        self.assertEqual(project.status(self.root)["stale"], "discover")

    def test_declarative_tests_are_required(self):
        self.artifacts("discover")
        path = self.root / "recovered/tests.yaml"
        path.unlink()
        with self.assertRaises((OSError, ValueError)):
            project.checkpoint(self.root, "discover")
        path.write_text("[]")
        with self.assertRaises(ValueError):
            project.checkpoint(self.root, "discover")
        path.write_text(yaml.safe_dump([{"id": "TEST-1", "origin": "observed", "evidence": ["E-1"], "scenarios": ["S-1"], "expect": {"returncode": 0}}]))
        project.checkpoint(self.root, "discover")
        self.assertEqual(project.status(self.root)["next"], "plan")

    def test_validation_requires_a_full_parity_pass(self):
        self.through("implement")
        self.artifacts("validate")
        for changes in ({"assessment": "scoped_pass"}, {"assessment": "incomplete"}, {"gaps": ["unknown feature"]}, {"errors": ["mismatch"]}, {"target_sha256": "wrong"}, {"inputs": {"recovered/product.md": "stale"}}, {"inputs": {}}):
            with self.subTest(changes=changes):
                self.parity(**changes)
                with self.assertRaises(ValueError):
                    project.checkpoint(self.root, "validate")
        self.parity()
        project.checkpoint(self.root, "validate")
        self.assertIsNone(project.status(self.root)["next"])

    def test_evidence_and_workspace_symlinks_fail(self):
        self.through("discover")
        (self.root / "recovered/evidence").rmdir()
        (self.root / "recovered/evidence").symlink_to(self.workspace, target_is_directory=True)
        self.assertEqual(project.status(self.root)["stale"], "discover")
        (self.root / "recovered/evidence").unlink()
        (self.root / "recovered/evidence").mkdir()
        real = self.base / "moved-agent"
        self.workspace.rename(real)
        self.workspace.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            project.status(self.root)


if __name__ == "__main__":
    unittest.main()
