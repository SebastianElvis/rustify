"""Seeded D-generate probes for options, option combinations, output modes, SQL, and input formats."""

import random

from cases import MODES, case

OPTIONS = [["-ascii"], ["-bail"], ["-batch"], ["-box"], ["-column"], ["-csv"], ["-echo"], ["-header"], ["-noheader"], ["-html"], ["-json"], ["-line"], ["-list"], ["-markdown"], ["-quote"], ["-table"], ["-tabs"], ["-readonly"], ["-safe"], ["-noinit"], ["-cmd", ".headers on"], ["-cmd", ".mode csv"], ["-separator", ";"], ["-separator", "<>"], ["-newline", "#\n"], ["-nullvalue", "NUL"], ["-escape", "symbol"], ["-escape", "ascii"], ["-escape", "off"], ["-screenwidth", "40"], ["-unsafe-testing"]]
MODE_OPTIONS = [["--quote", "off"], ["--quote", "on"], ["--quote", "sql"], ["--quote", "relaxed"], ["--quote", "csv"], ["--quote", "html"], ["--quote", "tcl"], ["--quote", "json"], ["--title", "on"], ["--title", "off"], ["--title", "always"], ["--title", "csv"], ["--title", "json"], ["--null", "~"], ["--colsep", "::"], ["--rowsep", "|\\n"], ["--wordwrap", "on"], ["--wordwrap", "off"], ["--widths", "3,0,-5"], ["--limits", "2,12"], ["--limits", "off"], ["--charlimit", "4"], ["--linelimit", "1"], ["--titlelimit", "2"], ["--escape", "symbol"], ["--escape", "ascii"], ["--align", "RCL"], ["--blob-quote", "hex"], ["--blob-quote", "tcl"], ["--blob-quote", "json"], ["--blob-quote", "size"], ["--blob-quote", "text"], ["--border", "off"], ["--rowcount", "on"], ["--textjsonb", "on"], ["--sw", "20"], ["--fpfmt", "%.3f"], ["--ifmt", "%05d"], ["--tablename", "dest"], ["--multiinsert", "30"], ["--reset"]]
DOTS = [".bail on", ".bail off", ".bail", ".changes on", ".changes", ".crlf on", ".crlf off", ".databases", ".dbconfig", ".dbconfig enable_fkey off", ".dump", ".echo on", ".echo", ".eqp on", ".eqp off", ".explain on", ".explain auto", ".fullschema", ".headers on", ".headers off", ".headers always", ".help .mode", ".help", ".indexes", ".limit", ".limit sql_length 99", ".mode", ".nullvalue", ".nullvalue X", ".parameter list", ".parameter set :p 3", ".print a b c", ".print", ".prompt x", ".quit now", ".schema", ".schema --nosys", ".separator", ".separator a b c", ".sha3sum", ".show", ".show x", ".tables", ".tables %", ".timeout", ".timeout abc", ".version", ".vfsname", ".width 1 2", ".width", ".frob", ".", "..", ".mode bogus", ".read", ".import", ".output a b", ".once", ".lint", ".lint bogus", ".expert --bogus", ".dbtotxt x", ".check", ".testcase", ".diskused", ".nonce", ".connection 9", ".auth on", ".auth off", ".intck 2", ".imposter"]
KEYWORDS = "SELECT FROM WHERE GROUP BY HAVING ORDER LIMIT OFFSET JOIN LEFT ON AS AND OR NOT NULL IS IN BETWEEN CASE WHEN THEN ELSE END INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE INDEX DROP ( ) , ; * + - / % || = <> < > <= >= ' \" ` [ ] 1 2.5 'x' x'0' ? :a @b $c t a b".split()
FUNCTIONS = ["abs", "length", "upper", "lower", "hex", "quote", "typeof", "round", "trim", "unicode", "char", "coalesce", "ifnull", "nullif", "instr", "substr", "replace", "printf", "format", "max", "min", "iif", "sign", "octet_length", "unhex", "concat", "concat_ws", "json_quote", "json_type", "json_valid", "sqrt", "ceil", "floor", "trunc", "mod", "pow", "log", "exp", "zeroblob", "likely", "unistr", "sha3", "decimal", "base64", "ieee754"]
SEED = 20261025


def value(rng):
    kind = rng.randrange(9)
    if kind == 0:
        return "NULL"
    if kind == 1:
        return str(rng.choice([0, 1, -1, 127, 128, 255, 256, 32767, 32768, 2**31 - 1, 2**31, 2**63 - 1, -2**63, 10**15, rng.randrange(-10**6, 10**6)]))
    if kind == 2:
        return repr(rng.choice([0.0, 0.5, -0.5, 1e-7, 1e15, 1e16, 3.141592653589793, 1e308, 2.5e-308, 123456789.125, rng.uniform(-1e6, 1e6)]))
    if kind == 3:
        return "x'" + rng.randbytes(rng.randrange(6)).hex() + "'"
    text = "".join(rng.choice(["a", "Z", " ", ",", "'", '"', "\\", "\t", "\n", "%", "_", "1", "-", ".", "e", "é", "中", "\U0001f600", "\x01", "|", ";", "<", "&"]) for _ in range(rng.randrange(8)))
    return "'" + text.replace("'", "''") + "'"


def expression(rng, depth=0):
    if depth > 3 or rng.random() < 0.3:
        return value(rng)
    form = rng.randrange(6)
    if form == 0:
        return f"({expression(rng, depth + 1)} {rng.choice(['+', '-', '*', '/', '%', '||', '&', '|', '<<', '>>', '=', '<>', '<', '>=', 'IS', 'IS NOT', 'AND', 'OR', 'LIKE', 'GLOB'])} {expression(rng, depth + 1)})"
    if form == 1:
        return f"{rng.choice(['-', '+', '~', 'NOT '])}{expression(rng, depth + 1)}"
    if form == 2:
        return f"CAST({expression(rng, depth + 1)} AS {rng.choice(['INTEGER', 'REAL', 'TEXT', 'BLOB', 'NUMERIC'])})"
    if form == 3:
        return f"CASE {expression(rng, depth + 1)} WHEN {expression(rng, depth + 1)} THEN {expression(rng, depth + 1)} ELSE {expression(rng, depth + 1)} END"
    if form == 4:
        return f"{expression(rng, depth + 1)} BETWEEN {expression(rng, depth + 1)} AND {expression(rng, depth + 1)}"
    return f"{rng.choice(FUNCTIONS)}({', '.join(expression(rng, depth + 1) for _ in range(rng.randrange(1, 4)))})"


def table(rng):
    rows = ", ".join("(" + ", ".join(value(rng) for _ in range(3)) + ")" for _ in range(rng.randrange(1, 6)))
    return f"CREATE TABLE g(a, \"b c\", d);\nINSERT INTO g VALUES {rows};\n"


def csv(rng):
    cells = lambda: ",".join(rng.choice(["1", "", "x", '"a,b"', '"q""q"', '"multi\nline"', " sp ", "2.5", "é"]) for _ in range(rng.randrange(1, 4)))
    return "\n".join(cells() for _ in range(rng.randrange(1, 6))) + rng.choice(["\n", "", "\r\n"])


def cases():
    rng = random.Random(SEED)
    out = []
    for n in range(120):
        args = [word for option in rng.sample(OPTIONS, rng.randrange(1, 5)) for word in option]
        out.append(case(f"cli-options/generated-{n}", table(rng) + "SELECT * FROM g;\nSELECT nope;\nSELECT 1 AS last;\n", args + [":memory:"] + (["SELECT 'arg'"] if rng.random() < 0.3 else [])))
    for n in range(len(MODES) * 8):
        options = " ".join(word for option in rng.sample(MODE_OPTIONS, rng.randrange(0, 4)) for word in option)
        headers = rng.choice(["", ".headers on\n", ".headers off\n"])
        out.append(case(f"mode-options/generated-{n}", f"{table(rng)}{headers}.mode {MODES[n % len(MODES)]} {options}\nSELECT * FROM g;\nSELECT a AS x FROM g LIMIT 1;\n"))
    for n in range(150):
        out.append(case(f"expressions/generated-{n}", ".mode quote\n" + "".join(f"SELECT {expression(rng)};\n" for _ in range(10))))
    for n in range(100):
        tokens = [rng.choice(KEYWORDS) for _ in range(rng.randrange(1, 12))]
        out.append(case(f"error-format/generated-{n}", "CREATE TABLE t(a, b);\n" + " ".join(tokens) + ";\nSELECT 'next';\n"))
    for n in range(80):
        out.append(case(f"dot-settings/generated-{n}", "CREATE TABLE t(a, b);\nINSERT INTO t VALUES(1, NULL);\n" + "".join(rng.choice(DOTS) + "\nSELECT * FROM t;\n" for _ in range(rng.randrange(1, 5)))))
    for n in range(60):
        mode = rng.choice(["--csv", "--ascii", ""]) if n % 2 else "--csv"
        out.append(case(f"dot-import/generated-{n}", f".import {mode} in.csv t\n.mode quote\nSELECT * FROM t;\n", files={"in.csv": csv(rng)}))
    return out
