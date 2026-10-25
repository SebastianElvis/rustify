import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


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
        path = (self.workspace if name in project.REQUIRED["plan"] else self.root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)

    def artifacts(self, phase):
        for name in project.REQUIRED[phase]:
            data = {"compatibility": [], "scope": []} if name == "recovered/contract.json" else {"content": True}
            self.write(name, json.dumps(data) if name.endswith(".json") else "content\n")
        if phase == "implement":
            self.write("implementation/src/main.rs", "fn main() {}\n")
            self.write("verification/checks.json", json.dumps({
                "status": "passed", "commands": [
                    {"command": ["cargo", name], "returncode": 0}
                    for name in ("fmt", "clippy", "test")
                ],
            }))
        if phase == "validate":
            self.write("implementation/target/release/base64", "candidate binary")
            candidate = self.root / "implementation/target/release/base64"
            self.write("verification/comparison.json", json.dumps({
                "status": "passed", "passed": 1, "failed": 0,
                "cases": [{"passed": True, "differences": []}],
                "executables": {
                    "reference": {"path": str(self.target), "sha256": project.digest(self.target)},
                    "candidate": {"path": str(candidate), "sha256": project.digest(candidate)},
                },
            }))

    def through(self, last):
        for phase in project.PHASES:
            self.artifacts(phase)
            project.checkpoint(self.root, phase)
            if phase == last:
                break

    def test_restart_and_ordered_checkpoints(self):
        self.assertEqual(project.status(self.root)["next"], "prepare")
        with self.assertRaises(ValueError):
            project.checkpoint(self.root, "plan")
        with self.assertRaises(ValueError):
            project.init(self.root, self.target, "cli")
        self.through("validate")
        self.assertEqual(project.status(str(self.root)), {"completed": list(project.PHASES), "next": None, "stale": None})

    def test_missing_empty_and_invalid_artifacts_fail(self):
        for data in (None, "", "  \n", "{}", "[]", "invalid", "null"):
            with self.subTest(data=data):
                if data is not None:
                    self.write("recovered/contract.json", data)
                with self.assertRaises((ValueError, OSError)):
                    project.checkpoint(self.root, "prepare")
        self.assertEqual(project.status(self.root)["next"], "prepare")

    def test_target_change_requires_new_project(self):
        self.target.write_bytes(b"different target")
        with self.assertRaisesRegex(ValueError, "new project"):
            project.status(self.root)
        with self.assertRaisesRegex(ValueError, "new project"):
            project.checkpoint(self.root, "prepare")

    def test_stale_artifact_invalidates_later_phases(self):
        self.through("validate")
        self.write("recovered/product.md", "The new evidence changes this product.\n")
        self.assertEqual(project.status(self.root), {"completed": ["prepare"], "next": "discover", "stale": "discover"})
        with self.assertRaises(ValueError):
            project.checkpoint(self.root, "validate")
        project.checkpoint(self.root, "discover")
        self.assertEqual(project.status(self.root)["next"], "plan")
        state = json.loads((self.root / "recovered/state.json").read_text())
        self.assertEqual(list(state["checkpoints"]), ["prepare", "discover"])

    def test_missing_artifact_reopens_phase(self):
        self.through("plan")
        (self.root / "recovered/ux.md").unlink()
        self.assertEqual(project.status(self.root)["stale"], "discover")

    def test_source_changes_and_additions_reopen_implementation(self):
        self.through("validate")
        self.write("implementation/src/main.rs", "fn main() { println!(\"change\"); }\n")
        self.assertEqual(project.status(self.root)["stale"], "implement")
        project.checkpoint(self.root, "implement")
        self.write("implementation/src/new.rs", "pub fn new() {}\n")
        self.assertEqual(project.status(self.root)["stale"], "implement")

    def test_all_implementation_inputs_reopen_implementation(self):
        self.through("validate")
        for name, content in (
            ("src/help.txt", "changed help"), ("src/version.txt", "changed version"),
            ("tests/empty.bin", ""), ("tests/malformed.json", "invalid JSON"),
            (".cargo/config.toml", '[build]\nrustflags = []\n'),
        ):
            with self.subTest(name=name):
                self.write("implementation/" + name, content)
                self.assertEqual(project.status(self.root)["stale"], "implement")
                project.checkpoint(self.root, "implement")
                path = self.root / "implementation" / name
                path.write_text(content + "changed")
                self.assertEqual(project.status(self.root)["stale"], "implement")
                project.checkpoint(self.root, "implement")
                path.unlink()
                self.assertEqual(project.status(self.root)["stale"], "implement")
                project.checkpoint(self.root, "implement")
        self.write("implementation/target/build-output", "ignored")
        self.write("implementation/.git/index", "ignored")
        self.assertIsNone(project.status(self.root)["stale"])
        link = self.root / "implementation/src/linked.txt"
        link.symlink_to(self.target)
        self.assertEqual(project.status(self.root)["stale"], "implement")
        with self.assertRaisesRegex(ValueError, "symlink"):
            project.checkpoint(self.root, "implement")

    def test_required_checks_use_the_latest_successful_result(self):
        self.through("plan")
        self.artifacts("implement")
        path = self.root / "verification/checks.json"
        valid = json.loads(path.read_text())
        for invalid in (
            {"status": "not-run", "commands": []},
            {"status": "passed", "commands": []},
            {"status": "failed", "commands": valid["commands"]},
            {"status": "passed", "commands": valid["commands"][:-1]},
            {"status": "passed", "commands": valid["commands"] + [
                {"args": ["cargo", "test"], "returncode": 101},
            ]},
        ):
            with self.subTest(invalid=invalid):
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    project.checkpoint(self.root, "implement")
        valid["commands"] += [
            {"args": ["cargo", "test"], "returncode": 101},
            {"args": ["cargo", "test"], "returncode": 0},
        ]
        path.write_text(json.dumps(valid))
        project.checkpoint(self.root, "implement")
        self.assertEqual(project.status(self.root)["next"], "validate")

    def test_failed_or_empty_comparison_cannot_complete(self):
        self.through("implement")
        self.artifacts("validate")
        path = self.root / "verification/comparison.json"
        original = json.loads(path.read_text())
        for changes in (
            {"status": "failed"}, {"failed": 1}, {"passed": 0},
            {"cases": []}, {"passed": 2}, {"cases": [{"passed": False, "differences": []}]},
            {"cases": [{"passed": True, "differences": ["stdout_b64"]}]},
        ):
            path.write_text(json.dumps({**original, **changes}))
            with self.assertRaises(ValueError):
                project.checkpoint(self.root, "validate")
        self.assertEqual(project.status(self.root)["next"], "validate")

    def test_wrong_target_or_changed_candidate_cannot_complete(self):
        self.through("implement")
        self.artifacts("validate")
        path = self.root / "verification/comparison.json"
        report = json.loads(path.read_text())
        report["executables"]["reference"]["sha256"] = "bad"
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "different target"):
            project.checkpoint(self.root, "validate")
        self.artifacts("validate")
        project.checkpoint(self.root, "validate")
        self.write("implementation/target/release/base64", "changed candidate")
        self.assertEqual(project.status(self.root)["stale"], "validate")
        with self.assertRaisesRegex(ValueError, "candidate changed"):
            project.checkpoint(self.root, "validate")

    def test_symlinks_and_external_artifacts_fail(self):
        (self.base / "outside").write_text('{"content": true}')
        (self.root / "recovered/contract.json").symlink_to(self.base / "outside")
        with self.assertRaisesRegex(ValueError, "symlink"):
            project.checkpoint(self.root, "prepare")
        with self.assertRaisesRegex(ValueError, "inside"):
            project.artifact(self.root, "../outside")
        with self.assertRaisesRegex(ValueError, "inside"):
            project.artifact(self.root, "/outside")

    def test_state_hashes_match_actual_artifacts(self):
        self.through("prepare")
        state = json.loads((self.root / "recovered/state.json").read_text())
        expected = hashlib.sha256((self.root / "recovered/contract.json").read_bytes()).hexdigest()
        self.assertEqual(state["checkpoints"]["prepare"]["recovered/contract.json"], expected)

    def test_workspace_stays_outside_the_three_project_directories(self):
        self.assertEqual({p.name for p in self.root.iterdir()}, {"recovered", "implementation", "verification"})
        self.assertEqual(self.workspace, self.base / ".target-rustify")
        self.assertFalse((self.root / "state.json").exists())
        self.assertTrue((self.root / "recovered/state.json").is_file())
        self.through("plan")
        self.assertTrue((self.workspace / "plan.json").is_file())
        self.assertTrue((self.workspace / "rust-design.md").is_file())
        self.assertFalse((self.root / "plan.json").exists())

    def test_custom_workspace_and_separation_guards(self):
        other = self.base / "other"
        custom = self.base / "agent"
        state = project.init(other, self.target, "cli", custom)
        self.assertEqual(state["work_dir"], str(custom))
        self.assertEqual(state["version"], 2)
        for workspace in (self.base / "unused", self.base / "unused/agent"):
            with self.subTest(workspace=workspace), self.assertRaisesRegex(ValueError, "outside"):
                project.init(self.base / "unused", self.target, "cli", workspace)
        link = self.base / "agent-link"
        link.symlink_to(custom, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            project.init(self.base / "unused", self.target, "cli", link)

    def test_plan_edits_reopen_planning(self):
        self.through("validate")
        self.write("plan.json", '{"tasks": ["changed"]}')
        self.assertEqual(project.status(self.root), {"completed": ["prepare", "discover"], "next": "plan", "stale": "plan"})
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
        self.through("prepare")
        self.artifacts("discover")
        path = self.root / "recovered/tests.json"
        path.unlink()
        with self.assertRaises((OSError, ValueError)):
            project.checkpoint(self.root, "discover")
        path.write_text("[]")
        with self.assertRaises(ValueError):
            project.checkpoint(self.root, "discover")
        path.write_text(json.dumps([{"id": "TEST-1", "origin": "observed", "evidence": ["E-1"], "scenarios": ["S-1"], "expect": {"returncode": 0}}]))
        project.checkpoint(self.root, "discover")
        self.assertEqual(project.status(self.root)["next"], "plan")

    def test_full_faithful_contract_requires_a_passing_parity_gate(self):
        self.through("implement")
        self.write("recovered/contract.json", json.dumps({"scope": {"mode": "full_product"}, "compatibility": {"mode": "faithful"}}))
        for phase in project.PHASES[:4]:
            project.checkpoint(self.root, phase)
        self.artifacts("validate")
        with self.assertRaises((ValueError, OSError)):
            project.checkpoint(self.root, "validate")
        valid = {"status": "passed", "full_parity_gate_pass": True, "errors": [], "gaps": [], "target_sha256": project.digest(self.target), "inputs": {"recovered/product.md": project.digest(self.root / "recovered/product.md")}}
        for changes in ({"status": "partial"}, {"full_parity_gate_pass": False}, {"gaps": ["unknown feature"]}, {"errors": ["mismatch"]}, {"target_sha256": "wrong"}, {"inputs": {"recovered/product.md": "stale"}}):
            self.write("verification/parity.json", json.dumps({**valid, **changes}))
            with self.assertRaises(ValueError):
                project.checkpoint(self.root, "validate")
        self.write("verification/parity.json", json.dumps(valid))
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
