import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("distinguish", ROOT / "eval/distinguish.py")
distinguish = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(distinguish)
AGENT = """#!/bin/sh
cat > /dev/null
printf 'id: p\\nargs: ["x\\\\ny"]\\n' > case.yaml
python3 probe.py A case.yaml > /dev/null
python3 probe.py B case.yaml > /dev/null
printf -- '- id: w\\n  args: ["y"]\\n' > witnesses.yaml
"""


class DistinguishTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup((temporary := tempfile.TemporaryDirectory()).cleanup)
        self.root = Path(temporary.name)
        self.echo = self.write("echo.sh", '#!/bin/sh\nprintf "%s\\n" "$1"\n')
        self.upper = self.write("upper.sh", '#!/bin/sh\nprintf "%s\\n" "$1" | tr a-z A-Z\n')

    def write(self, name, text):
        path = self.root / name
        path.write_text(text)
        path.chmod(0o755)
        return path

    def test_game_results_require_blind_paired_observations(self):
        for name, reference, candidate, agent, budget, expected in [
            ("same", self.echo, self.echo, AGENT, 10, ("passed", 2, 0, None, 0, 2)),
            ("search-error", self.echo, self.echo, AGENT + "python3 -c 'import os,yaml; p=yaml.safe_load(open(os.environ[\"DISTINGUISH_CONFIG\"]))[\"log\"]; rows=list(yaml.safe_load_all(open(p))); open(p,\"w\").write(yaml.safe_dump_all([dict(r,view={\"error\":\"sandbox denied\"}) for r in rows],explicit_start=True))'\n", 10, ("invalid", 2, 0, None, 0, 2)),
            ("different", self.echo, self.upper, AGENT, 10, ("failed", 2, 2, 2, 0, 2)),
            ("variable", self.write("pid.sh", '#!/bin/sh\necho "$$"\n'), self.echo, AGENT, 10, ("incomplete", 2, 0, None, 2, 2)),
            ("mixed", self.write("mixed.sh", '#!/bin/sh\nif [ "$1" = y ]; then echo "$$"; else printf "%s\\n" "$1"; fi\n'), self.upper, AGENT.replace("id: w", "id: p") + "python3 probe.py A case.yaml > /dev/null\n", 10, ("failed", 3, 1, 2, 1, 2)),
            ("repeat-error", self.write("repeat-error.sh", f'#!/bin/sh\nif [ "$1" = y ]; then echo "$$"; exit; fi\nif [ "$1" = z ]; then n=$(cat "{self.root / "count"}" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "{self.root / "count"}"; if [ "$n" = 2 ]; then sleep 10; fi; fi\nprintf "%s\\n" "$1"\n'), self.upper, AGENT.replace("id: w", "id: p") + "python3 probe.py A case.yaml > /dev/null\nprintf -- '- id: p\\n  args: [\"z\"]\\n' >> witnesses.yaml\n", 10, ("invalid", 3, 1, 2, 1, 3)),
            ("budget", self.echo, self.upper, AGENT, 1, ("invalid", 1, 2, None, 0, 2)),
            ("concurrent", None, self.write("slow.sh", '#!/bin/sh\nsleep 0.2\nprintf "%s\\n" "$1"\n'), AGENT.replace("case.yaml > /dev/null\n", "case.yaml > /dev/null &\n") + "wait\n", 1, ("invalid", 1, 0, None, 0, 2)),
            ("timeout", None, self.write("sleep.sh", '#!/bin/sh\nsleep 1\n'), AGENT, 10, ("invalid", 2, 0, None, 0, 2)),
            ("empty", self.echo, self.echo, "#!/bin/sh\ncat > /dev/null\n", 10, ("invalid", 0, 0, None, 0, 0)),
            ("crash", self.echo, self.echo, "#!/bin/sh\nexit 1\n", 10, ("invalid", 0, 0, None, 0, 0)),
            ("limited", self.echo, self.echo, AGENT + "exit 1\n", 10, ("invalid", 2, 0, None, 0, 2)),
            ("leak", self.echo, self.echo, AGENT + f"echo '{self.echo.resolve()}' >&2\n", 10, ("invalid", 2, 0, None, 0, 2)),
        ]:
            with self.subTest(name=name):
                report = distinguish.play(reference or candidate, candidate, str(self.write("agent.sh", agent)), budget, "tool", self.root / name, 0.01 if name == "timeout" else 5, 7)
                self.assertEqual(tuple(report[field] for field in ("status", "probes", "witnesses", "query_complexity", "inconclusive", "replayed_cases")), expected)
                self.assertEqual(yaml.safe_load((self.root / name / "report.yaml").read_text()), report)
                self.assertEqual((len({row["input"]["id"] for row in report["replays"]}), sum("reference_repeat" in row and (not row["repeatability_differences"] or not row["passed"]) for row in report["replays"])), (report["replayed_cases"], report["replayed_cases"]))
                self.assertTrue(all(row["case"]["args"] == ["x\ny"] for row in yaml.safe_load_all((self.root / name / "probes.log").read_text() if report["probes"] else "")))


if __name__ == "__main__":
    unittest.main()
