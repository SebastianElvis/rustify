"""Convert the upstream Tcl tests of the pinned SQLite source into sqlite3 shell probes.

The converter reads each `test/*.test` file in order. It keeps the tests that use only
`execsql`, `db eval`, `catchsql`, `catchcmd`, `do_execsql_test`, `do_catchsql_test`, and
`integrity_check` with literal arguments. It runs the SQL of one database connection in one
shell process in `.mode quote`, with a marker query before each step. The Tcl expectation
validates each converted probe on the reference. The gate is the exact view of the reference.
"""

import re
import zipfile

import runner

SOURCE = {"name": "sqlite-src-3540100.zip", "url": "https://sqlite.org/2026/sqlite-src-3540100.zip", "sha256": "387e7f6cad4797b17848c07d453dc6606917bb356a6cfe5a3abafd38c240c71b"}
TESTS = re.compile(r"^\s*(do_\w*test\w*|integrity_check)\s", re.M)
FEATURES = [
    (r"^shell", "cli-options"), (r"json", "json"), (r"window", "window"), (r"wal", "wal"), (r"trigger", "triggers"),
    (r"view", "views"), (r"join", "join"), (r"^(with|cte)", "cte"), (r"compound|union|values", "compound"),
    (r"insert|update|delete|upsert|returning|conflict", "dml"), (r"date|time|julian", "datetime"),
    (r"trans|savepoint|journal|rollback", "transactions"), (r"pragma", "pragma"),
    (r"vacuum|analyze|attach|reindex|explain|eqp", "maintenance"), (r"collat|nocase", "collation"),
    (r"affinity|types|cast|strict|numcast", "affinity"), (r"null", "null"), (r"rowid|autoinc|without", "rowid"),
    (r"unique|notnull|check|fkey|gencol|default", "constraints"), (r"corrupt|integ", "integrity"),
    (r"vtab|series|tvf|carray|decimal|ieee|sha|base64|base85", "virtual-tables"),
    (r"agg|sum|avg|count|minmax|group|having", "aggregate"), (r"func|substr|printf|instr|trim|round|hex|quote|format", "scalar-functions"),
    (r"select|distinct|limit|orderby|where|sort|index", "select"), (r"^sub|exists|^in\d", "subquery"),
    (r"expr|like|glob|between|case|e_", "expressions"), (r"alter|table|schema|drop|create", "ddl"),
    (r"btree|pager|io|lock|page|big|backup|filefmt|format", "file-format"),
]
ESCAPES = {"a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\n": " "}


def words(text):
    """Split Tcl source into commands of (kind, raw word) pairs."""
    command, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r" or (c == "\\" and text[i + 1:i + 2] == "\n"):
            i += 1 if c != "\\" else 2
        elif c in "\n;":
            if command:
                yield command
            command, i = [], i + 1
        elif c == "#" and not command:
            while i < n and text[i] != "\n":
                i += 2 if text[i] == "\\" else 1
        elif c in "{\"":
            close, depth, j = ("}" if c == "{" else '"'), 1, i + 1
            while j < n and depth:
                if text[j] == "\\":
                    j += 1
                elif c == "{" and text[j] == "{":
                    depth += 1
                elif text[j] == close:
                    depth -= 1
                j += 1
            command.append(("brace" if c == "{" else "quote", text[i + 1:j - 1]))
            i = j
        else:
            j, depth = i, 0
            while j < n and (depth or text[j] not in " \t\r\n;"):
                depth += {"[": 1, "]": -1}.get(text[j], 0)
                j += 2 if text[j] == "\\" else 1
            command.append(("bare", text[i:j]))
            i = j
    if command:
        yield command


def unescape(value):
    def one(match):
        code = match.group(1)
        if code[0] in "xu" and len(code) > 1:
            return chr(int(code[1:], 16))
        if code[0].isdigit():
            return chr(int(code, 8))
        return ESCAPES.get(code, code)
    return re.sub(r"\\(x[0-9a-fA-F]{1,2}|u[0-9a-fA-F]{1,4}|[0-7]{1,3}|.|\n)", one, value, flags=re.S)


def literal(word):
    """Return the value of a word without substitution, or None when Tcl would substitute."""
    kind, value = word
    if kind == "brace":
        return value
    if "$" in value or "[" in value:
        return None
    return unescape(value)


def splitlist(text):
    return [value if kind == "brace" else unescape(value) for command in words(text.replace(";", "\\;").replace("#", "\\#")) for kind, value in command]


def tcl_list(values):
    def quote(value):
        if value == "":
            return "{}"
        if not re.search(r"[\s{}\[\]\"\\$;#]", value):
            return value
        if value.count("{") == value.count("}") and not value.endswith("\\"):
            return "{" + value + "}"
        return re.sub(r"([\s{}\[\]\"\\$;])", r"\\\1", value)
    return " ".join(map(quote, values))


def matches(result, expected):
    """Apply the comparison rules of `do_test` in tester.tcl."""
    if re.fullmatch(r"[~#]?/.*/", expected, re.S):
        negate, pattern = expected[0] == "~", expected[2:-1] if expected[0] in "~#" else expected[1:-1]
        if expected[0] == "#":
            return False
        try:
            ok = fnmatch(result, pattern) if pattern.startswith("*") else re.search(pattern.replace("#", "[-0-9.]+"), result, re.S) is not None
        except re.error:
            return False
        return ok != negate
    if re.fullmatch(r"~?\*.*\*", expected, re.S):
        return fnmatch(result, expected.lstrip("~")) != expected.startswith("~")
    if result == expected:
        return True
    a, b = splitlist(result), splitlist(expected)
    try:
        return len(a) == len(b) and all(x == y or abs(float(x) - float(y)) <= 1e-12 * max(1, abs(float(y))) for x, y in zip(a, b))
    except ValueError:
        return False


def fnmatch(text, pattern):
    return re.fullmatch("".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern), text, re.S) is not None


def values(segment):
    """Parse `.mode quote` rows into Tcl values. Return None for any other text."""
    token = re.compile(r"NULL|unistr\('((?:[^']|'')*)'\)|'((?:[^']|'')*)'|[xX]'([0-9a-fA-F]*)'|([^,\n']+)")
    result, i = [], 0
    while i < len(segment):
        match = token.match(segment, i)
        if not match:
            return None
        if match.group(1) is not None:
            result.append(re.sub(r"\\(u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|\\)", lambda m: "\\" if m.group(1) == "\\" else chr(int(m.group(1)[1:], 16)), match.group(1).replace("''", "'")))
        elif match.group(2) is not None:
            result.append(match.group(2).replace("''", "'"))
        elif match.group(3) is not None:
            result.append(bytes.fromhex(match.group(3)).decode("latin-1"))
        elif match.group(4) is not None:
            number = match.group(4)
            if re.fullmatch(r"-?\d+", number):
                result.append(number)
            else:
                try:
                    result.append({"inf": "Inf", "-inf": "-Inf"}.get(repr(float(number)), repr(float(number))))
                except ValueError:
                    return None
        else:
            result.append("")
        i = match.end()
        if i < len(segment) and segment[i] not in ",\n":
            return None
        i += 1
    return result


def error(segment):
    found = re.search(r"^(?:Parse error|Runtime error|Error)(?: near line \d+)?: (.*?)(?: \(\d+\))?$", segment, re.M)
    return found.group(1) if found else None


class Converter:
    """Turn the Tcl commands of one test file into probe actions."""

    def __init__(self):
        self.actions, self.prefix, self.db, self.stop, self.unsupported = [], "", "test.db", False, []

    def name(self, word):
        name = literal(word) or word[1]
        return f"{self.prefix}-{name}" if self.prefix and name[:1].isdigit() else name

    def step(self, command):
        """Return an action for a result command, or None."""
        head = command[0][1]
        args = [literal(word) for word in command[1:]]
        if None in args:
            return None
        if (head == "execsql" or (head == "db" and args[:1] == ["eval"])) and len(command) == 2 + (head == "db"):
            return {"kind": "sql", "sql": args[-1], "check": "list"}
        if head == "catchsql" and len(command) == 2:
            return {"kind": "sql", "sql": args[0], "check": "catch"}
        if head in ("catchcmd", "catchcmdex") and len(command) in (2, 3):
            stdin = args[1] if len(args) > 1 else ""
            return {"kind": "cli", "args": [literal(word) or word[1] for command in words(args[0]) for word in command], "stdin": stdin if head == "catchcmdex" else stdin + "\n", "keep": head == "catchcmdex"}
        return None

    def state(self, command):
        """Apply a state command. Return False for an unknown command."""
        head, args = command[0][1], [literal(word) for word in command[1:]]
        if head in ("source", "finish_test", "proc", "unset") or (head == "set" and args[:1] in (["testdir"], ["testprefix"], ["::testprefix"])):
            if head == "set" and args[0] != "testdir" and args[1] is not None:
                self.prefix = args[1]
            return True
        if head == "return":
            self.stop = True
            return True
        if head in ("forcedelete", "delete_file") and None not in args:
            self.actions.append({"kind": "delete", "files": [arg for arg in args if not arg.startswith("-")]})
            return True
        if head == "reset_db" or (head == "db" and args == ["close"]) or (head == "sqlite3" and len(args) == 2 and args[0] == "db" and args[1]):
            self.actions += [{"kind": "close"}] + ([{"kind": "delete", "files": ["test.db", "test.db-journal", "test.db-wal"]}] if head == "reset_db" else [])
            self.db = "test.db" if head == "reset_db" else args[1] if head == "sqlite3" else self.db
            return True
        if head == "ifcapable" and len(command) >= 3 and command[2][0] == "brace":
            if not (args[0] or "").startswith("!"):
                self.walk(command[2][1])
            elif len(command) == 5:
                self.walk(command[4][1])
            return True
        action = self.step(command)
        if action:
            self.actions.append({**action, "db": self.db})
            return True
        if head == "db":
            self.unsupported.append([word[1] for word in command])
        return False

    def test(self, command):
        head = command[0][1]
        if head == "integrity_check" and len(command) == 2:
            return self.name(command[1]), [[("bare", "execsql"), ("brace", "PRAGMA integrity_check")]], "ok"
        if head == "do_execsql_test" and len(command) in (3, 4) and not command[1][1].startswith("-"):
            expected = literal(command[3]) if len(command) == 4 else ""
            return self.name(command[1]), [[("bare", "execsql"), command[2]]], None if expected is None else tcl_list(splitlist(expected))
        if head == "do_catchsql_test" and len(command) == 4:
            return self.name(command[1]), [[("bare", "catchsql"), command[2]]], literal(command[3])
        if head in ("do_test", "do_test_with_ansi_output") and len(command) == 4 and command[2][0] == "brace":
            return self.name(command[1]), list(words(command[2][1])), literal(command[3])
        return None

    def walk(self, text):
        for command in words(text):
            if self.stop or self.unsupported:
                return
            found = self.test(command)
            if found and found[2] is not None and found[1]:
                name, body, expected = found
                for item in body[:-1]:
                    if not self.state(item):
                        break
                else:
                    action = self.step(body[-1])
                    if action:
                        self.actions.append({**action, "db": self.db, "name": name, "expected": expected})
                continue
            if not found:
                self.state(command)


def convert(text):
    converter = Converter()
    converter.walk(text)
    return converter.actions + [{"kind": "unsupported", "command": command} for command in converter.unsupported]


def run(binary, actions):
    """Run the actions of one file. Return one result per action."""
    runner.reset()
    results, batch = [None] * len(actions), []

    def flush():
        if not batch:
            return
        script = ".mode quote\n" + "".join(f"SELECT '@@{index}';\n{actions[index]['sql']}\n;\n" for index in batch) + "SELECT '@@end';\n"
        output = runner.invoke(binary, [actions[batch[0]]["db"]], script.encode(), merge=True)
        parts = re.split(rb"^'@@(\d+|end)'\n", output["stdout"], flags=re.M)
        found = {int(parts[k]): parts[k + 1] for k in range(1, len(parts) - 1, 2) if parts[k] != b"end"}
        for index in batch:
            results[index] = {"output": found.get(index, b"<missing marker>"), "error": output["error"]}
        batch.clear()

    for index, action in enumerate(actions):
        if action["kind"] == "sql":
            if batch and actions[batch[0]]["db"] != action["db"]:
                flush()
            batch.append(index)
            continue
        flush()
        if action["kind"] == "delete":
            for name in action["files"]:
                path = runner.SANDBOX / name
                if path.is_file() and runner.SANDBOX.resolve() in path.resolve().parents:
                    path.unlink()
        elif action["kind"] == "cli":
            output = runner.invoke(binary, action["args"], action["stdin"].encode())
            results[index] = output
    flush()
    return results


def tcl_result(action, result):
    """Rebuild the Tcl value of a probe from its shell view."""
    if action["kind"] == "cli":
        message = result["stdout"].decode("utf-8", "surrogateescape") + result["stderr"].decode("utf-8", "surrogateescape")
        if result["returncode"] and not result["stderr"]:
            message += "child process exited abnormally"
        if not action["keep"] and message.endswith("\n"):
            message = message[:-1]
        return tcl_list(["1" if result["returncode"] or result["stderr"] else "0", message])
    segment = result["output"].decode("utf-8", "surrogateescape")
    if action["check"] == "catch" and error(segment) is not None:
        return tcl_list(["1", error(segment)])
    rows = values(segment)
    if rows is None:
        return None
    return tcl_list(rows) if action["check"] == "list" else tcl_list(["0", tcl_list(rows)])


def files(archive):
    with zipfile.ZipFile(archive) as bundle:
        return {name.split("/test/", 1)[1]: bundle.read(name).decode("utf-8", "replace") for name in sorted(bundle.namelist()) if re.fullmatch(r"[^/]+/test/[^/]+\.test", name)}


def evaluate(reference, candidate, name, text):
    """Return the report of one upstream test file."""
    actions = convert(text)
    feature = next((feature for pattern, feature in FEATURES if re.search(pattern, name)), "sql-engine")
    first, second, other = run(reference, actions), run(reference, actions), run(candidate, actions)
    rows, counts = [], {"unstable": 0, "unmatched": 0, "unsupported": [action["command"] for action in actions if action["kind"] == "unsupported"]}
    for action, a, b, c in zip(actions, first, second, other):
        if "name" not in action:
            continue
        if a != b and not (a.get("error") or b.get("error")):
            counts["unstable"] += 1
            continue
        result = tcl_result(action, a)
        if not (a.get("error") or b.get("error")) and (result is None or not matches(result, action["expected"])):
            counts["unmatched"] += 1
            continue
        passed = a == c and not (a.get("error") or b.get("error"))
        rows.append({"id": f"{feature}/{name}/{action['name']}", "passed": passed, **({} if passed else {"input": {key: action[key] for key in action if key not in ("expected",)}, "expected": action["expected"], "reference": a, "repeat": b, "candidate": c, "differences": ["execution_error"] if a.get("error") or b.get("error") or c.get("error") else ["result"]})})
    failed = sum(not row["passed"] for row in rows)
    return {"status": "invalid" if any(row and row.get("error") for row in first + second) else "incomplete" if any(counts.values()) or (not rows and TESTS.search(text)) else "failed" if failed else "passed", "passed": len(rows) - failed, "failed": failed, "tests": len(TESTS.findall(text)), "converted": len(rows), **counts, "cases": rows}
