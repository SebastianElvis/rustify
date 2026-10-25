"""Run the upstream Ninja tests and adapt the upstream parser test inputs to black-box scenarios."""

import ast
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

import yaml

import harness
from cases import case, step

ROOT = Path(__file__).resolve().parent
PIN = yaml.safe_load((ROOT / "reference.yaml").read_text())
SCRIPTS = {"output_test": "misc/output_test.py", "jobserver_test": "misc/jobserver_test.py"}
HELPERS = ("misc/jobserver_pool.py", "misc/jobserver_test_helper.py")
FEATURES = {
    "test_issue_1418": "status", "test_issue_1214": "status", "test_issue_1966": "rspfile", "test_issue_2499": "smart-terminal",
    "test_pr_1685": "tool-recompact", "test_issue_2048": "build-log", "test_pr_2540": "keep-going", "test_depfile_directory_creation": "depfile",
    "test_status": "status", "test_ninja_status_default": "status", "test_ninja_status_quiet": "status", "test_entering_directory_on_stdout": "options",
    "test_tool_inputs": "tool-inputs", "test_tool_compdb_targets": "tool-compdb", "test_tool_multi_inputs": "tool-multi-inputs",
    "test_explain_output": "restat", "test_issue_2586": "pools", "test_issue_2621": "dyndep", "test_issue_2681": "interrupt",
}
DRIVER = """
import importlib.util, sys, unittest
sys.path.insert(0, sys.argv[3])
import yaml
spec = importlib.util.spec_from_file_location("upstream_test", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
class Result(unittest.TestResult):
    outcomes = {}
    def addSuccess(self, test):
        self.outcomes[test.id()] = ["passed", ""]
    def addFailure(self, test, error):
        self.outcomes[test.id()] = ["failed", self._exc_info_to_string(error, test)]
    addError = addFailure
    def addSkip(self, test, reason):
        self.outcomes[test.id()] = ["skipped", reason]
unittest.defaultTestLoader.loadTestsFromModule(module).run(Result())
open(sys.argv[2], "w").write(yaml.safe_dump(Result.outcomes, sort_keys=False))
"""
LITERAL = r'(?:\s*"(?:[^"\\\n]|\\.)*")+'
TEST = re.compile(r"\nTEST(?:_F)?\(\w+, (\w+)\)(.*?)(?=\nTEST|\Z)", re.S)
INPUT = re.compile(r"(?:ParseTest|AssertParse|Parse)\((" + LITERAL + r")|kInput\[\]\s*=\s*(" + LITERAL + ")")
PARSE = re.compile(r"AssertParse\(&(\w+),\s*(" + LITERAL + ")")
CREATE = re.compile(r'fs_\.Create\("([\w./ -]+)",\s*(' + LITERAL + ")")
TARGET = re.compile(r'AddTarget\("([^"]+)"')
CAT = "rule cat\n  command = cat $in > $out\n"
GRAPHS = {"build_test": ("incremental", "build cat1: cat in1\nbuild cat2: cat in1 in2\nbuild cat12: cat cat1 cat2\n", {"in1": "", "in2": ""}), "graph_test": ("incremental", "", {}), "clean_test": ("tool-clean", "", {})}
DEPFILE = "rule cc\n  command = cp src.d out.d && touch out\n  depfile = out.d\n{deps}build out: cc\n"
DYNDEP = "rule touch\n  command = touch $out\nrule cp\n  command = cp $in $out\nbuild dd: cp dd.in\nbuild out otherout: touch || dd\n  dyndep = dd\n"


def sources():
    """Read the upstream test files from the pinned source archive."""
    downloads = harness.REPOSITORY / "work/downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = harness.load("build_reference", harness.REPOSITORY / "scripts/build_reference.py").fetch(PIN["sources"][0], downloads)
    prefix = PIN["workdir"] + "/"
    with tarfile.open(archive) as bundle:
        return {item.name[len(prefix):]: bundle.extractfile(item).read().decode() for item in bundle.getmembers() if item.isfile() and re.fullmatch(r"(misc/[\w.]+\.py|src/\w+_test\.cc)", item.name[len(prefix):])}


def python_attempt(executable, files, script):
    """Run one upstream Python test file against one executable and return each outcome."""
    with tempfile.TemporaryDirectory(prefix="rustify-ninja-upstream-") as directory:
        root = Path(directory)
        (root / "misc").mkdir()
        # The issue_2621 probe uses one job to fix the command completion order.
        for name in (script, *HELPERS):
            (root / name).write_text(files[name].replace('            "-v",\n            r"""[1/4] printf', '            "-j1 -v",\n            r"""[1/4] printf') if name == script else files[name])
        (root / "work").mkdir()
        (root / "work/ninja").symlink_to(executable)
        env = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC", "HOME": directory, "PATH": "/usr/bin:/bin"}
        # The upstream tests run `script`, which forwards EOF from a closed stdin to the pty, so stdin stays open.
        process = subprocess.Popen([sys.executable, "-I", "-c", DRIVER, str(root / script), str(root / "outcomes.yaml"), str(Path(yaml.__file__).resolve().parent.parent)], cwd=root / "work", env=env, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            process.wait(timeout=600)
        finally:
            process.stdin.close()
            process.kill()
        path = root / "outcomes.yaml"
        return {key.rsplit(".", 1)[-1]: value for key, value in yaml.safe_load(path.read_text()).items()} if path.exists() else {}


def python_report(reference, candidate, files, script):
    results = {label: python_attempt(binary, files, script) for label, binary in (("reference", reference), ("candidate", candidate))}
    names = sorted(set(results["reference"]) | set(results["candidate"]) | set(re.findall(r"\n    def (test_\w+)", files[script])))
    rows = [{"id": f"{FEATURES.get(name, 'jobserver')}/{name}", **{label: dict(zip(("outcome", "detail"), result.get(name, ["missing", ""]))) for label, result in results.items()}} for name in names]
    for row in rows:
        row["passed"] = row["reference"]["outcome"] == row["candidate"]["outcome"] == "passed"
    failed = sum(not row["passed"] for row in rows)
    return {"status": "failed" if failed or not rows else "passed", "passed": len(rows) - failed, "failed": failed, "cases": rows}


def literal(text):
    return "".join(ast.literal_eval(part) for part in re.findall(r'"(?:[^"\\\n]|\\.)*"', text))


def inputs(text):
    """Yield each test name, input index, and input text of an upstream C++ parser test file."""
    for name, body in TEST.findall(text):
        for index, match in enumerate(INPUT.finditer(body)):
            yield name, index, literal(match.group(1) or match.group(2))


def unit_scenarios(files):
    """Turn the parser test inputs into scenarios with the same outcome checks as the replay cases."""
    groups = {"manifest_parser_test": [], "depfile_parser_test": [], "dyndep_parser_test": []}
    for name, index, text in inputs(files["src/manifest_parser_test.cc"]):
        groups["manifest_parser_test"].append(case(f"manifest-language/{name}-{index}", {"input": text}, step("-f", "input", "-n", "-v", "-k", "0"), step("-f", "input", "-t", "targets", "all")))
    for name, index, text in inputs(files["src/depfile_parser_test.cc"]):
        for mode, deps in (("gcc", "  deps = gcc\n"), ("depfile", "")):
            groups["depfile_parser_test"].append(case(f"depfile/{name}-{index}-{mode}", {"build.ninja": DEPFILE.format(deps=deps), "src.d": text}, step("-j1"), step("-t", "deps"), step("-j1", "-d", "explain")))
    for name, index, text in inputs(files["src/dyndep_parser_test.cc"]):
        groups["dyndep_parser_test"].append(case(f"dyndep/{name}-{index}", {"build.ninja": DYNDEP, "dd.in": text}, step("-j1", "-v"), step("-t", "query", "out"), step("-j1", "-d", "explain")))
    for stem, (feature, fixture, created) in GRAPHS.items():
        groups[stem] = [graph_scenario(f"{feature}/{name}-{stem}", body, fixture, created, stem == "clean_test") for name, body in TEST.findall(files[f"src/{stem}.cc"]) if PARSE.search(body)]
    return groups


def leaves(manifest):
    """Return an empty file for each plain input path that no build statement produces, as the test fixtures do."""
    outputs, inputs = set(), set()
    for line in manifest.split("\n"):
        if line.startswith("build ") and ":" in line and "$" not in line:
            left, right = line[6:].split(":", 1)
            outputs.update(left.replace("|", " ").split())
            inputs.update(right.replace("|@", " ").replace("|", " ").split()[1:])
    return {name: "" for name in sorted(inputs - outputs) if ".." not in name.split("/") and not name.startswith("/")}


def graph_scenario(identity, body, fixture, created, clean):
    """Replay each manifest of a C++ graph test as a dry run with the files that the test creates."""
    files = {**created, **{name: literal(text) for name, text in CREATE.findall(body) if ".." not in name.split("/")}}
    targets = list(dict.fromkeys(TARGET.findall(body)))
    steps = []
    for state, text in dict.fromkeys((state, literal(text)) for state, text in PARSE.findall(body)):
        manifest = ("" if "rule cat\n" in text else CAT) + (fixture if state == "state_" else "") + text
        if not steps:
            files = {**leaves(manifest), **files}
        chosen = [target for target in targets if target in manifest]
        steps += [step("-n", "-v", "-k", "0", "-j1", *chosen, write={"build.ninja": manifest}), step("-n", "-d", "explain", "-j1", *chosen)]
        steps += [step("-n", "-v", "-t", "clean"), step("-t", "clean", *chosen)] if clean else []
    return case(identity, files, *steps, step("-t", "targets", "all"))


def inventory(files):
    """Count the upstream unit tests per file and the tests that the adapted reports exercise."""
    adapted = {"src/" + name + ".cc" for name in unit_scenarios(files)}
    return {name: {"tests": len(TEST.findall(text)), "adapted": name in adapted} for name, text in sorted(files.items()) if name.endswith("_test.cc")}
