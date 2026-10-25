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
printf 'id: p\\nargs: ["x"]\\n' > case.yaml
python3 probe.py A case.yaml > /dev/null
python3 probe.py B case.yaml > /dev/null
printf -- '- id: w\\n  args: ["y"]\\n' > witnesses.yaml
"""


class DistinguishTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.agent = self.write("agent.sh", AGENT)
        self.echo = self.write("echo.sh", '#!/bin/sh\nprintf "%s\\n" "$1"\n')
        self.upper = self.write("upper.sh", '#!/bin/sh\nprintf "%s\\n" "$1" | tr a-z A-Z\n')

    def write(self, name, text):
        path = self.root / name
        path.write_text(text)
        path.chmod(0o755)
        return path

    def play(self, candidate, name):
        return distinguish.play(self.echo, candidate, str(self.agent), 10, "tool", self.root / name, 5, 7)

    def test_identical_programs_have_no_witness(self):
        report = self.play(self.echo, "same")
        self.assertEqual((report["status"], report["probes"], report["witnesses"]), ("passed", 2, 0))

    def test_different_programs_give_confirmed_witnesses(self):
        report = self.play(self.upper, "different")
        self.assertEqual((report["status"], report["witnesses"], report["query_complexity"]), ("failed", 2, 1))
        self.assertEqual(yaml.safe_load((self.root / "different/report.yaml").read_text())["witnesses"], 2)

    def test_budget_stops_probes(self):
        report = distinguish.play(self.echo, self.upper, str(self.agent), 1, "tool", self.root / "budget", 5, 7)
        self.assertEqual(report["probes"], 1)


if __name__ == "__main__":
    unittest.main()
