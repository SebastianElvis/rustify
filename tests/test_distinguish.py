import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("distinguish", ROOT / "scripts/distinguish.py")
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
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.echo = self.write("echo.sh", '#!/bin/sh\nprintf "%s\\n" "$1"\n')
        self.upper = self.write("upper.sh", '#!/bin/sh\nprintf "%s\\n" "$1" | tr a-z A-Z\n')

    def write(self, name, text):
        path = self.root / name
        path.write_text(text)
        path.chmod(0o755)
        return path

    def test_game_results_require_blind_paired_observations(self):
        for name, candidate, agent, budget, expected in [
            ("same", self.echo, AGENT, 10, ("passed", 2, 0, None)),
            ("search-error", self.echo, AGENT + "python3 -c 'import os,yaml; p=yaml.safe_load(open(os.environ[\"DISTINGUISH_CONFIG\"]))[\"log\"]; rows=list(yaml.safe_load_all(open(p))); open(p,\"w\").write(yaml.safe_dump_all([dict(r,view={\"error\":\"sandbox denied\"}) for r in rows],explicit_start=True))'\n", 10, ("invalid", 2, 0, None)),
            ("different", self.upper, AGENT, 10, ("failed", 2, 2, 2)),
            ("budget", self.upper, AGENT, 1, ("invalid", 1, 2, None)),
            ("concurrent", self.write("slow.sh", '#!/bin/sh\nsleep 0.2\nprintf "%s\\n" "$1"\n'), AGENT.replace("case.yaml > /dev/null\n", "case.yaml > /dev/null &\n") + "wait\n", 1, ("invalid", 1, 0, None)),
            ("timeout", self.write("sleep.sh", '#!/bin/sh\nsleep 1\n'), AGENT, 10, ("invalid", 2, 0, None)),
            ("empty", self.echo, "#!/bin/sh\ncat > /dev/null\n", 10, ("invalid", 0, 0, None)),
            ("crash", self.echo, "#!/bin/sh\nexit 1\n", 10, ("invalid", 0, 0, None)),
            ("limited", self.echo, AGENT + "exit 1\n", 10, ("invalid", 2, 0, None)),
            ("leak", self.echo, AGENT + f"echo '{self.echo.resolve()}' >&2\n", 10, ("invalid", 2, 0, None)),
        ]:
            with self.subTest(name=name):
                report = distinguish.play(candidate if name in {"concurrent", "timeout"} else self.echo, candidate, str(self.write("agent.sh", agent)), budget, "tool", self.root / name, 0.01 if name == "timeout" else 5, 7)
                self.assertEqual(tuple(report[field] for field in ("status", "probes", "witnesses", "query_complexity")), expected)
                self.assertEqual(yaml.safe_load((self.root / name / "report.yaml").read_text()), report)
                if report["probes"]:
                    self.assertEqual(next(yaml.safe_load_all((self.root / name / "probes.log").read_text()))["case"]["args"], ["x\ny"])


if __name__ == "__main__":
    unittest.main()
