"""Hidden sqlite3 cases. Each case id is `<feature-id>/<name>` with a feature from grading.yaml."""

import base64

DATA = """CREATE TABLE dept(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, budget REAL);
CREATE TABLE emp(id INTEGER PRIMARY KEY, name TEXT, dept INTEGER REFERENCES dept(id), salary INTEGER, boss INTEGER, note);
INSERT INTO dept VALUES(1,'eng',1000.5),(2,'ops',NULL),(3,'sales',250),(4,'empty',0);
INSERT INTO emp VALUES(1,'ann',1,120,NULL,'lead'),(2,'bob',1,100,1,NULL),(3,'cid',2,90,1,x'00ff'),
(4,'dee',2,95,3,3.5),(5,'eve',3,70,1,'a,b'),(6,'fay',NULL,60,5,'say "hi"'),(7,'Gus',3,70,5,'line1
line2'),(8,'hal',1,NULL,2,'');
"""

TRICKY = "SELECT 1 AS i, 2.5 AS r, 'text' AS t, NULL AS n, x'0102ff' AS b, 'a,b' AS comma, 'q\"uote' AS dq, 'it''s' AS sq, 'tab\tx' AS tab, 'nl\nx' AS nl, 'caf\u00e9 \u4e2d' AS u, -0.0 AS z, 9223372036854775807 AS big, 1e300 AS huge, '' AS empty;\n"

MODES = ["list", "csv", "column", "line", "json", "box", "qbox", "table", "markdown", "psql", "html", "insert", "quote", "tcl", "ascii", "tabs", "split", "count", "off", "jatom", "jobject", "c", "batch", "tty"]


def encode(text):
    return base64.b64encode(text.encode("utf-8", "surrogateescape")).decode("ascii")


def case(identity, script="", args=(), files=None):
    item = {"id": identity, "args": list(args), "stdin_b64": encode(script)}
    if files:
        item["files"] = {name: encode(value) for name, value in files.items()}
    return item


def core():
    """Shell basics and core SQL."""
    out = [
        case("sql-input/stdin-default-memory", "SELECT 1, 'a';\nSELECT 2;\n"),
        case("sql-input/argument", args=[":memory:", "SELECT 1+1", "SELECT 'x'"]),
        case("sql-input/argument-and-stdin", "SELECT 'stdin';\n", [":memory:", "SELECT 'arg'"]),
        case("sql-input/multiple-per-line", "SELECT 1; SELECT 2;SELECT 3\n;\n"),
        case("sql-input/no-trailing-semicolon", "SELECT 42"),
        case("sql-input/comments", "-- c1\nSELECT /* c2 */ 1; -- c3\n/* multi\nline */ SELECT 2;\n"),
        case("sql-input/incomplete-at-eof", "SELECT 'open;\n"),
        case("sql-input/empty", ""),
        case("sql-input/crlf", "SELECT 1;\r\nSELECT 'a\r\nb';\r\n"),
        case("cli-options/bail", "SELECT 1;\nSELECT nope;\nSELECT 2;\n", ["-bail"]),
        case("cli-options/no-bail", "SELECT 1;\nSELECT nope;\nSELECT 2;\n"),
        case("cli-options/cmd", "SELECT 1, NULL;\n", ["-cmd", ".mode csv", "-cmd", ".nullvalue N"]),
        case("cli-options/batch", "SELECT 1;\n", ["-batch"]),
        case("cli-options/header", "SELECT 1 AS a, 2 AS b;\n", ["-header"]),
        case("cli-options/noheader", "SELECT 1 AS a;\n", ["-header", "-noheader"]),
        case("cli-options/csv", TRICKY, ["-csv"]),
        case("cli-options/json", TRICKY, ["-json"]),
        case("cli-options/csv-header", "SELECT 1 AS a, 'x y' AS b;\n", ["-csv", "-header"]),
        case("cli-options/unknown", args=["-bogus"]),
        case("cli-options/missing-argument", args=["-cmd"]),
        case("cli-options/version", args=["-version"]),
        case("cli-options/help", args=["-help"]),
        case("cli-options/double-dash", "SELECT 1;\n", ["--", ":memory:"]),
        case("error-format/parse", "SELECT * FROM;\n"),
        case("error-format/no-table", "SELECT * FROM missing;\n"),
        case("error-format/no-column", "CREATE TABLE t(a);\nSELECT b FROM t;\n"),
        case("error-format/runtime-constraint", "CREATE TABLE t(a UNIQUE NOT NULL);\nINSERT INTO t VALUES(1);\nINSERT INTO t VALUES(1);\nINSERT INTO t VALUES(NULL);\n"),
        case("error-format/argument", args=[":memory:", "SELECT nope"]),
        case("error-format/multiline", "SELECT 1,\n  2,\n  nope\nFROM (SELECT 1);\n"),
        case("error-format/unknown-dot", ".frobnicate\n"),
        case("error-format/exit-status", "SELECT 1;\nSELECT x;\n"),
        case("mode-list/default", DATA + "SELECT * FROM emp ORDER BY id;\n"),
        case("mode-list/show-mode", ".mode\n"),
        case("mode-list/tricky", TRICKY),
        case("mode-csv/tricky", ".mode csv\n" + TRICKY),
        case("mode-csv/headers", ".mode csv\n.headers on\n" + DATA + "SELECT * FROM emp;\n"),
        case("mode-column/data", ".mode column\n" + DATA + "SELECT * FROM emp;\n"),
        case("mode-column/headers-off", ".mode column\n.headers off\nSELECT 'abc', 12345, NULL, 1.5;\n"),
        case("mode-column/tricky", ".mode column\n" + TRICKY),
        case("mode-line/data", ".mode line\n" + DATA + "SELECT * FROM dept;\n"),
        case("mode-line/tricky", ".mode line\n" + TRICKY),
        case("mode-json/data", ".mode json\n" + DATA + "SELECT * FROM emp;\n"),
        case("mode-json/tricky", ".mode json\n" + TRICKY),
        case("mode-json/empty-result", ".mode json\nSELECT 1 WHERE 0;\n"),
        case("mode-options/headers", ".headers on\n" + DATA + "SELECT name, salary FROM emp WHERE id<3;\n.headers off\nSELECT 1 AS hidden;\n"),
        case("mode-options/headers-usage", ".headers\n.headers maybe\n"),
        case("mode-list/separator", ".separator ;\nSELECT 1,2;\n.separator , !\nSELECT 3,4;SELECT 5,6;\n"),
        case("mode-list/separator-escapes", '.separator "\\t" "\\r\\n"\nSELECT 1,2;\n'),
        case("mode-options/nullvalue", ".nullvalue (null)\nSELECT NULL, 1;\n.mode csv\nSELECT NULL;\n.mode line\nSELECT NULL AS x;\n"),
        case("dot-schema/tables", DATA + "CREATE TABLE zeta(x);\nCREATE TEMP TABLE tmp(y);\n.tables\n.tables e%\n"),
        case("dot-schema/schema", DATA + "CREATE INDEX emp_dept ON emp(dept);\n.schema\n.schema emp\n.schema nothing\n"),
        case("dot-schema/schema-indent", DATA + ".schema --indent dept\n"),
        case("dot-read/read", ".read script.sql\nSELECT 'after';\n", files={"script.sql": "SELECT 'inside';\n.mode csv\nSELECT 1,2;\n"}),
        case("dot-read/read-missing", ".read missing.sql\nSELECT 1;\n"),
        case("dot-read/quit", "SELECT 1;\n.quit\nSELECT 2;\n"),
        case("dot-read/exit-code", "SELECT 1;\n.exit 3\nSELECT 2;\n"),
        case("ddl/create-drop", "CREATE TABLE t(a INT, b TEXT);\nDROP TABLE t;\nDROP TABLE t;\nDROP TABLE IF EXISTS t;\nCREATE TABLE IF NOT EXISTS u(x);\nCREATE TABLE u(x);\n"),
        case("ddl/create-index", DATA + "CREATE INDEX i1 ON emp(salary DESC, name);\nCREATE UNIQUE INDEX i2 ON emp(name);\nCREATE UNIQUE INDEX i3 ON emp(salary);\nSELECT name, tbl_name FROM sqlite_schema WHERE type='index' ORDER BY 1;\n"),
        case("dml/insert-forms", "CREATE TABLE t(a, b DEFAULT 'd');\nINSERT INTO t VALUES(1,2);\nINSERT INTO t(a) VALUES(3);\nINSERT INTO t DEFAULT VALUES;\nINSERT INTO t SELECT a*10, b FROM t;\nSELECT rowid, * FROM t;\n"),
        case("dml/update-delete", DATA + "UPDATE emp SET salary = salary + 1 WHERE dept = 1;\nDELETE FROM emp WHERE salary IS NULL OR salary < 70;\nSELECT id, salary FROM emp;\nSELECT changes(), total_changes();\n"),
        case("select/where-order-limit", DATA + "SELECT name FROM emp WHERE salary BETWEEN 70 AND 100 ORDER BY salary DESC, name LIMIT 3 OFFSET 1;\nSELECT name FROM emp ORDER BY 1 LIMIT 2, 2;\n"),
        case("select/group-having", DATA + "SELECT dept, count(*), sum(salary), avg(salary), min(name), max(salary) FROM emp GROUP BY dept HAVING count(*) > 1 ORDER BY dept;\n"),
        case("select/distinct", DATA + "SELECT DISTINCT dept FROM emp ORDER BY 1;\nSELECT count(DISTINCT salary) FROM emp;\n"),
        case("join/inner-left", DATA + "SELECT e.name, d.name FROM emp e JOIN dept d ON e.dept = d.id ORDER BY e.id;\nSELECT d.name, e.name FROM dept d LEFT JOIN emp e ON e.dept = d.id ORDER BY d.id, e.id;\nSELECT a.name, b.name FROM emp a, emp b WHERE a.boss = b.id ORDER BY a.id;\n"),
        case("subquery/forms", DATA + "SELECT name FROM emp WHERE salary > (SELECT avg(salary) FROM emp) ORDER BY 1;\nSELECT name FROM dept WHERE id IN (SELECT dept FROM emp) ORDER BY 1;\nSELECT name FROM dept d WHERE NOT EXISTS (SELECT 1 FROM emp WHERE dept=d.id);\nSELECT (SELECT count(*) FROM emp WHERE dept=d.id) FROM dept d;\nSELECT * FROM (SELECT dept, max(salary) m FROM emp GROUP BY dept) ORDER BY m;\n"),
        case("aggregate/functions", DATA + "SELECT count(*), count(note), sum(salary), total(salary), avg(salary), min(salary), max(salary), group_concat(name), group_concat(name, '-') FROM emp;\nSELECT sum(x), total(x), avg(x), count(x) FROM (SELECT 1 x WHERE 0);\n"),
        case("scalar-functions/text", "SELECT length('h\u00e9'), upper('abc'), lower('ABC'), substr('hello', 2, 3), substr('hello', -3), trim('  x  '), ltrim('xxa', 'x'), rtrim('ayy', 'y'), replace('aaa', 'a', 'b'), instr('hello', 'l'), hex('AB'), quote('it''s'), char(72, 105), unicode('A'), typeof(1), coalesce(NULL, 2), ifnull(NULL, 'n'), nullif(1, 1), iif(1, 'y', 'n'), abs(-3), round(2.567, 2), round(2.5), printf('%5.2f|%-4d|%s|%x', 3.14159, 42, 'z', 255);\n"),
        case("affinity/columns", "CREATE TABLE t(i INTEGER, r REAL, t TEXT, n NUMERIC, b BLOB, x);\nINSERT INTO t VALUES('12','12','12','12','12','12'),(3.0,3,3,'3.0','3.0',3.0),('1e2','abc',1.5,'0x10',x'01',' 7 ');\nSELECT typeof(i), i, typeof(r), r, typeof(t), t, typeof(n), n, typeof(b), typeof(x) FROM t;\nSELECT '10' < 9, 10 < '9', '10' = 10, CAST('12abc' AS INTEGER), CAST(3.9 AS INTEGER), CAST(12 AS TEXT) || 'x';\n"),
        case("null/semantics", "SELECT NULL = NULL, NULL IS NULL, NULL IS NOT 1, 1 + NULL, NULL AND 0, NULL OR 1, NULL IN (1, NULL), 1 IN (1, NULL), coalesce(NULL, NULL);\nCREATE TABLE t(a);\nINSERT INTO t VALUES(NULL),(1),(NULL);\nSELECT count(*), count(a), sum(a) FROM t;\nSELECT a FROM t ORDER BY a;\nSELECT a FROM t ORDER BY a DESC;\nSELECT DISTINCT a FROM t;\n"),
        case("rowid/behavior", "CREATE TABLE t(a);\nINSERT INTO t VALUES('x'),('y');\nDELETE FROM t WHERE a='y';\nINSERT INTO t VALUES('z');\nINSERT INTO t(rowid, a) VALUES(100, 'w');\nINSERT INTO t VALUES('v');\nSELECT rowid, oid, _rowid_, a FROM t;\nCREATE TABLE p(id INTEGER PRIMARY KEY, v);\nINSERT INTO p(v) VALUES(1);\nINSERT INTO p VALUES(9223372036854775806, 2);\nINSERT INTO p(v) VALUES(3);\nSELECT * FROM p;\nSELECT last_insert_rowid();\n"),
        case("constraints/basic", "CREATE TABLE t(id INTEGER PRIMARY KEY, u TEXT UNIQUE, n TEXT NOT NULL, c INT CHECK(c > 0), d DEFAULT 5);\nINSERT INTO t(u, n, c) VALUES('a', 'x', 1);\nINSERT INTO t(u, n, c) VALUES('a', 'y', 1);\nINSERT INTO t(u, c) VALUES('b', 1);\nINSERT INTO t(u, n, c) VALUES('c', 'z', 0);\nINSERT INTO t(id, u, n, c) VALUES(1, 'd', 'w', 2);\nINSERT OR IGNORE INTO t(u, n, c) VALUES('a', 'q', 3);\nINSERT OR REPLACE INTO t(u, n, c) VALUES('a', 'r', 4);\nSELECT * FROM t;\n"),
        case("transactions/rollback", "CREATE TABLE t(a);\nBEGIN;\nINSERT INTO t VALUES(1);\nROLLBACK;\nBEGIN TRANSACTION;\nINSERT INTO t VALUES(2);\nCOMMIT;\nSELECT * FROM t;\nCOMMIT;\nBEGIN;\nBEGIN;\nEND;\n"),
        case("expressions/operators", "SELECT 7/2, 7%3, 7.0/2, -7/2, 1<<4, 255>>2, 5&3, 5|3, ~5, 'a'||'b'||1, 3 BETWEEN 1 AND 5, 'abc' LIKE 'A%', 'abc' GLOB 'A*', CASE 2 WHEN 1 THEN 'one' WHEN 2 THEN 'two' END, CASE WHEN 0 THEN 1 ELSE 'else' END, 1/0, 9223372036854775807+1, -9223372036854775808-1, 2*4611686018427387904;\n"),
    ]
    return out


def extended():
    """Output modes, dot commands, and advanced SQL."""
    out = [case(f"mode-{feature}/{mode}", f".mode {mode}\n.headers on\n" + TRICKY + DATA + "SELECT * FROM emp ORDER BY id;\nSELECT * FROM dept WHERE 0;\n") for feature, modes in (("table", ["box", "qbox", "table", "markdown", "psql"]), ("markup", ["html", "tcl"]), ("sql", ["insert", "quote"]), ("delimited", ["ascii", "tabs", "split", "count", "off"]), ("json", ["jatom", "jobject"]), ("list", ["c", "batch", "tty"])) for mode in modes]
    out += [
        case("mode-options/width", ".mode column\n.width 3 -6 0\n.headers on\n" + DATA + "SELECT name, salary, note FROM emp;\n.width\nSELECT 1;\n"),
        case("mode-options/wordwrap", ".mode box --wordwrap on --widths 8,8\nSELECT 'the quick brown fox jumps over' AS a, 'x' AS b;\n.mode table --wrap 5\nSELECT 'abcdefghijkl' AS v;\n"),
        case("mode-options/quote-title", ".mode list --quote on --title on\n" + TRICKY + ".mode csv --title off\n" + TRICKY),
        case("mode-options/limits", ".mode box --limits 2,10\nSELECT 'line1\nline2\nline3' AS a, 'abcdefghijklmnopqrstuvwxyz' AS b;\n"),
        case("mode-options/escape", ".mode list --escape symbol\nSELECT 'a' || char(1) || char(27) || 'b';\n.mode list --escape ascii\nSELECT 'a' || char(1) || 'b';\n.mode list --escape off\nSELECT 'a' || char(1) || 'b';\n"),
        case("mode-options/align-rowcount", ".mode table --align LCR --rowcount on\n.headers on\nSELECT 'a' AS x, 'bb' AS y, 'ccc' AS z UNION ALL SELECT 'dddd', 'e', 'f';\n"),
        case("mode-options/insert-tablename", ".mode insert target\nSELECT 1, 'a''b', NULL, x'00', 2.5;\n.mode insert --multiinsert 40\nSELECT value FROM generate_series(1, 9);\n"),
        case("mode-options/verbose", ".mode -v\n.mode csv\n.mode -v\n"),
        case("mode-options/unknown", ".mode nosuch\n.mode list --bogus\n"),
        case("mode-options/once", ".mode csv --once\nSELECT 1,2;\nSELECT 3,4;\n"),
        case("mode-options/tag-reset", ".mode csv --tag mine\n.mode list\n.mode mine\nSELECT 1,2;\n.mode --reset\nSELECT 3,4;\n"),
        case("dot-dump/full", DATA + "CREATE INDEX ix ON emp(name);\nCREATE VIEW v AS SELECT name FROM emp;\nCREATE TRIGGER tr AFTER INSERT ON emp BEGIN SELECT 1; END;\nCREATE TABLE seq(id INTEGER PRIMARY KEY AUTOINCREMENT, v);\nINSERT INTO seq(v) VALUES(1),(2);\n.dump\n"),
        case("dot-dump/table-and-options", DATA + ".dump dept\n.dump --data-only emp\n.dump --preserve-rowids dept\n.dump --nosys --newlines emp\n"),
        case("dot-schema/fullschema", DATA + "ANALYZE;\n.fullschema\n"),
        case("dot-schema/indexes", DATA + "CREATE INDEX a ON emp(name);\nCREATE INDEX b ON dept(budget);\n.indexes\n.indexes emp\n.indices dept\n"),
        case("dot-output/print", '.print hello "quoted words" \'single\' \\t\n.print\n.print "\\x41\\101\\n"\n'),
        case("dot-output/echo", ".echo on\nSELECT 1;\n.mode csv\n.echo off\nSELECT 2;\n"),
        case("dot-output/output-stdout", ".output stdout\nSELECT 1;\n.output\nSELECT 2;\n"),
        case("dot-settings/show", ".show\n.mode csv\n.headers on\n.nullvalue NULL\n.separator x y\n.show\n"),
        case("dot-settings/changes", "CREATE TABLE t(a);\n.changes on\nINSERT INTO t VALUES(1),(2);\nUPDATE t SET a=a+1;\nSELECT 1;\n.changes off\nDELETE FROM t;\n"),
        case("dot-settings/bail", ".bail on\nSELECT 1;\nSELECT nope;\nSELECT 2;\n"),
        case("dot-settings/limit", ".limit\n.limit length 10\nSELECT length(zeroblob(5)), 'abcdefghijkl';\n"),
        case("dot-settings/dbconfig", ".dbconfig\n.dbconfig defensive on\n.dbconfig defensive\n"),
        case("dot-settings/timeout-prompt", ".timeout 10\n.prompt a b\n.crlf\nSELECT 1;\n"),
        case("dot-parameter/bind", ".parameter init\n.parameter set :a 5\n.parameter set @b 'txt'\n.parameter set $c NULL\n.parameter list\nSELECT :a + 1, @b, $c, ?1;\n.parameter unset :a\n.parameter list\n.parameter clear\nSELECT :a;\n"),
        case("dot-info/version", ".version\nSELECT sqlite_version(), sqlite_source_id();\n"),
        case("dot-info/sha3sum", DATA + ".sha3sum\n.sha3sum --sha3-224 emp\n.sha3sum --schema\n"),
        case("dot-info/vfs", ".vfsname\n.vfslist\n.vfsinfo\n"),
        case("dot-info/dbtotxt", DATA + ".dbtotxt\n"),
        case("dot-info/check-testcase", ".testcase t1\nSELECT 1;\n.check 1\n.testcase t2\nSELECT 2;\n.check 3\n"),
        case("dot-explain/eqp", DATA + "CREATE INDEX ix ON emp(dept);\n.eqp on\nSELECT * FROM emp WHERE dept=1;\n.eqp off\nEXPLAIN QUERY PLAN SELECT * FROM emp JOIN dept ON emp.dept=dept.id ORDER BY emp.name;\n"),
        case("dot-explain/explain", "CREATE TABLE t(a);\nEXPLAIN SELECT a FROM t WHERE a > 1;\n.explain off\nEXPLAIN SELECT 1;\n"),
        case("dot-explain/expert", DATA + ".expert\nSELECT * FROM emp WHERE salary = 5;\n"),
        case("dot-explain/lint", DATA + "CREATE TABLE child(p REFERENCES emp(salary));\n.lint fkey-indexes\n"),
        case("dot-system/help", ".help\n.help mode\n.help -all\n.help nosuch\n"),
        case("dot-system/safe", ".shell echo hi\n", ["-safe"]),
        case("dot-system/safe-functions", "SELECT readfile('x');\nATTACH 'other.db' AS o;\n", ["-safe"]),
        case("dot-database/databases", "ATTACH ':memory:' AS aux;\n.databases\n"),
        case("compound/operators", "SELECT 1 UNION SELECT 2 UNION SELECT 1;\nSELECT 1 UNION ALL SELECT 1;\nSELECT 1 INTERSECT SELECT 1;\nSELECT 1 EXCEPT SELECT 1;\nVALUES(1,'a'),(2,'b');\nSELECT 3 AS x UNION SELECT 1 ORDER BY x DESC LIMIT 1;\n"),
        case("cte/recursive", "WITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM c WHERE n<10) SELECT group_concat(n) FROM c;\nWITH a AS (SELECT 2 x), b AS MATERIALIZED (SELECT x*3 y FROM a) SELECT * FROM a, b;\n" + DATA + "WITH RECURSIVE chain(id, name, depth) AS (SELECT id, name, 0 FROM emp WHERE boss IS NULL UNION ALL SELECT e.id, e.name, depth+1 FROM emp e JOIN chain ON e.boss = chain.id) SELECT * FROM chain ORDER BY depth, id;\n"),
        case("window/functions", DATA + "SELECT name, dept, salary, row_number() OVER w, rank() OVER w, dense_rank() OVER w, percent_rank() OVER w, cume_dist() OVER w, ntile(2) OVER w, lag(salary) OVER w, lead(salary, 1, -1) OVER w, first_value(name) OVER w, last_value(name) OVER w, nth_value(name, 2) OVER w FROM emp WINDOW w AS (PARTITION BY dept ORDER BY salary DESC) ORDER BY dept, salary DESC, name;\nSELECT id, sum(salary) OVER (ORDER BY id ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING), avg(salary) OVER (ORDER BY id RANGE UNBOUNDED PRECEDING), count(*) OVER (ORDER BY salary GROUPS BETWEEN CURRENT ROW AND 1 FOLLOWING EXCLUDE TIES) FROM emp ORDER BY id;\n"),
        case("views/basic", DATA + "CREATE VIEW rich AS SELECT name, salary FROM emp WHERE salary > 90;\nSELECT * FROM rich ORDER BY 1;\nCREATE VIEW v2(a, b) AS SELECT 1, 2;\nSELECT * FROM v2;\nINSERT INTO rich VALUES('x', 1);\nDROP VIEW rich;\nSELECT * FROM rich;\n"),
        case("triggers/basic", "CREATE TABLE t(a);\nCREATE TABLE log(msg);\nCREATE TRIGGER ti AFTER INSERT ON t BEGIN INSERT INTO log VALUES('ins ' || new.a); END;\nCREATE TRIGGER tu BEFORE UPDATE ON t WHEN new.a > 100 BEGIN SELECT RAISE(ABORT, 'too big'); END;\nCREATE TRIGGER td AFTER DELETE ON t FOR EACH ROW BEGIN INSERT INTO log VALUES('del ' || old.a); END;\nINSERT INTO t VALUES(1),(2);\nUPDATE t SET a = 500;\nDELETE FROM t WHERE a = 1;\nSELECT * FROM log;\nCREATE VIEW v AS SELECT a FROM t;\nCREATE TRIGGER vi INSTEAD OF INSERT ON v BEGIN INSERT INTO t VALUES(new.a * 2); END;\nINSERT INTO v VALUES(21);\nSELECT * FROM t;\n"),
        case("dml/upsert-returning", "CREATE TABLE kv(k PRIMARY KEY, v, n DEFAULT 0);\nINSERT INTO kv VALUES('a', 1, 0) RETURNING *;\nINSERT INTO kv(k, v) VALUES('a', 2) ON CONFLICT(k) DO UPDATE SET v = excluded.v, n = n + 1 RETURNING k, v, n;\nINSERT INTO kv(k, v) VALUES('a', 3) ON CONFLICT DO NOTHING;\nUPDATE kv SET v = v * 10 RETURNING v AS ten;\nDELETE FROM kv RETURNING k;\nREPLACE INTO kv(k, v) VALUES('b', 1);\nUPDATE OR FAIL kv SET k = 'c' FROM (SELECT 1) WHERE k = 'b';\nSELECT * FROM kv;\n"),
        case("ddl/alter", "CREATE TABLE t(a, b);\nINSERT INTO t VALUES(1, 2);\nALTER TABLE t ADD COLUMN c DEFAULT 'z';\nALTER TABLE t RENAME COLUMN a TO x;\nALTER TABLE t RENAME TO u;\nALTER TABLE u DROP COLUMN b;\nSELECT * FROM u;\nSELECT sql FROM sqlite_schema;\nALTER TABLE u ADD COLUMN d NOT NULL;\n"),
        case("constraints/foreign-keys", "PRAGMA foreign_keys = ON;\nCREATE TABLE p(id INTEGER PRIMARY KEY);\nCREATE TABLE c(pid REFERENCES p(id) ON DELETE CASCADE);\nINSERT INTO p VALUES(1);\nINSERT INTO c VALUES(1);\nINSERT INTO c VALUES(2);\nDELETE FROM p;\nSELECT count(*) FROM c;\nPRAGMA foreign_key_check;\n"),
        case("constraints/generated-strict", "CREATE TABLE g(a INT, b INT GENERATED ALWAYS AS (a * 2) VIRTUAL, c TEXT AS (a || 'x') STORED);\nINSERT INTO g(a) VALUES(3);\nSELECT * FROM g;\nCREATE TABLE s(i INTEGER, t TEXT, a ANY) STRICT;\nINSERT INTO s VALUES(1, 'a', 1.5);\nINSERT INTO s VALUES('x', 'a', 1);\nINSERT INTO s VALUES('2', 3, x'00');\nSELECT typeof(i), typeof(t), typeof(a) FROM s;\n"),
        case("rowid/without-rowid", "CREATE TABLE w(k TEXT PRIMARY KEY, v) WITHOUT ROWID;\nINSERT INTO w VALUES('b', 2), ('a', 1);\nSELECT * FROM w;\nSELECT rowid FROM w;\nCREATE TABLE ai(id INTEGER PRIMARY KEY AUTOINCREMENT, v);\nINSERT INTO ai(v) VALUES(1),(2);\nDELETE FROM ai;\nINSERT INTO ai(v) VALUES(3);\nSELECT * FROM ai;\nSELECT * FROM sqlite_sequence;\n"),
        case("collation/builtin", "SELECT 'a' = 'A', 'a' = 'A' COLLATE NOCASE, 'a ' = 'a' COLLATE RTRIM;\nCREATE TABLE t(x TEXT COLLATE NOCASE);\nINSERT INTO t VALUES('b'),('A'),('a'),('B');\nSELECT x FROM t ORDER BY x, x COLLATE BINARY;\nSELECT x FROM t ORDER BY x COLLATE BINARY;\nSELECT DISTINCT x FROM t;\nSELECT 'x10' < 'x9' COLLATE uint, 'x10' < 'x9';\n"),
        case("transactions/savepoint", "CREATE TABLE t(a);\nSAVEPOINT s1;\nINSERT INTO t VALUES(1);\nSAVEPOINT s2;\nINSERT INTO t VALUES(2);\nROLLBACK TO s2;\nRELEASE s1;\nSELECT * FROM t;\nROLLBACK TO nope;\nBEGIN IMMEDIATE;\nCOMMIT;\nBEGIN EXCLUSIVE;\nROLLBACK;\n"),
        case("pragma/common", "PRAGMA page_size;\nPRAGMA encoding;\nPRAGMA journal_mode;\nPRAGMA user_version = 7;\nPRAGMA user_version;\nPRAGMA application_id;\nCREATE TABLE t(a INTEGER PRIMARY KEY, b TEXT NOT NULL DEFAULT 'x');\nCREATE INDEX tb ON t(b);\nPRAGMA table_info(t);\nPRAGMA table_xinfo(t);\nPRAGMA index_list(t);\nPRAGMA index_info(tb);\nPRAGMA integrity_check;\nPRAGMA quick_check;\nPRAGMA compile_options;\nPRAGMA nosuch;\nSELECT * FROM pragma_table_list ORDER BY name;\n"),
        case("maintenance/attach-vacuum-analyze", "ATTACH ':memory:' AS aux;\nCREATE TABLE aux.t(a);\nINSERT INTO aux.t VALUES(1);\nSELECT * FROM aux.t;\nSELECT name FROM pragma_database_list;\nDETACH aux;\nSELECT * FROM aux.t;\nCREATE TABLE t(a);\nCREATE INDEX ta ON t(a);\nINSERT INTO t VALUES(1),(1),(2);\nANALYZE;\nSELECT * FROM sqlite_stat1;\nVACUUM;\nREINDEX;\n"),
        case("datetime/fixed", "SELECT date('2024-02-28', '+1 day'), date('2023-02-28', '+1 day'), datetime('2024-01-31 10:20:30', '+1 month'), time('12:00', '-90 minutes'), julianday('2000-01-01'), unixepoch('2024-01-01'), strftime('%Y|%m|%d|%H|%M|%S|%j|%w|%W|%s|%f|%%', '2024-03-05 06:07:08.9'), datetime(1700000000, 'unixepoch'), date('2024-01-15', 'start of month', '+1 month', '-1 day'), timediff('2024-03-01', '2024-01-01'), date('2024-01-01', 'weekday 0'), datetime('2024-01-01T12:00:00Z'), date('nonsense'), datetime(2460000.5);\n"),
        case("math/functions", "SELECT sqrt(2), pow(2, 10), power(2, 0.5), exp(1), ln(10), log(100), log10(1000), log(2, 8), log2(8), ceil(1.2), floor(-1.2), trunc(-2.7), sin(0), cos(0), tan(1), asin(1), acos(1), atan(1), atan2(1, 1), pi(), degrees(pi()), radians(180), mod(7, 3), sign(-4), sqrt(-1);\n"),
        case("scalar-functions/more", "SELECT format('%q|%Q|%w|%z', 'it''s', NULL, 'a\"b', 'z'), printf('%,d|%.3e|%g|%c|%10.3s|%-+5d', 1234567, 12345.678, 0.0001, 'xyz', 'abcdef', 7), concat('a', NULL, 1), concat_ws('-', 'a', NULL, 'b'), octet_length('\u00e9'), unhex('41FF'), unhex('4'), unistr('\\u0041\\0042'), unistr_quote('a\nb'), substring('hello', 2), string_agg(x, ';') , likely(1), unlikely(0), likelihood(1, 0.5), zeroblob(3), typeof(zeroblob(3)), soundex IS NULL FROM (SELECT 'a' x UNION ALL SELECT 'b') LEFT JOIN (SELECT NULL soundex);\n"),
        case("expressions/like-glob-regexp", "SELECT 'abc' LIKE 'a_c', 'a%c' LIKE 'a\\%c' ESCAPE '\\', 'ABC' LIKE 'abc', 'abc' GLOB '[a-c]*', 'abc' GLOB '*[!x]', 'abc' REGEXP '^a.c$', 'abc' NOT REGEXP 'b', regexpi('ABC', 'abc'), like('a%', 'abc'), glob('a*', 'abc');\n"),
        case("expressions/cast-and-types", "SELECT CAST('3.7e2' AS REAL), CAST(' 42 ' AS INTEGER), CAST(x'414243' AS TEXT), CAST('abc' AS BLOB), CAST(1e100 AS INTEGER), CAST('-0' AS REAL), CAST('0x1F' AS INTEGER), 0x1F, 1_000_000, typeof(1.0), typeof('1'), typeof(x''), 1e-400, 1.0/3, 100000000000000000000.0, 0.1 + 0.2, 2.0 * 3;\n"),
    ]
    return out


def complete():
    """JSON, virtual tables, shell extensions, and the remaining surface."""
    return [
        case("json/functions", "SELECT json(' { \"a\" : [1, 2.5, \"x\", null, true] } '), json_array(1, 'two', NULL, json('[3]')), json_object('k', 1, 'n', NULL), json_extract('{\"a\":{\"b\":[10,20]}}', '$.a.b[1]', '$.a'), '{\"a\":1}' -> '$.a', '{\"a\":\"s\"}' ->> 'a', json_insert('{}', '$.x', 1), json_replace('{\"x\":1}', '$.x', 2), json_set('[1]', '$[#]', 2), json_remove('[1,2,3]', '$[1]'), json_patch('{\"a\":1,\"b\":2}', '{\"b\":null,\"c\":3}'), json_type('[1]'), json_type('{\"a\":1.5}', '$.a'), json_valid('{'), json_valid('{}'), json_quote('a\"b'), json_array_length('[1,2]'), json_error_position('[1,'), json_pretty('{\"a\":[1,{\"b\":2}]}');\n"),
        case("json/jsonb-and-aggregates", "SELECT hex(jsonb('{\"a\":1}')), json(jsonb('[1,\"x\"]')), jsonb_extract(jsonb('{\"a\":[1]}'), '$.a'), json_group_array(x), json_group_object(x, x*x) FROM (SELECT 1 x UNION ALL SELECT 2);\nSELECT key, value, type, atom, path FROM json_each('{\"a\":1,\"b\":[2,3]}');\nSELECT key, value, type, fullkey FROM json_tree('{\"a\":{\"b\":[1]}}');\nSELECT json('{bad');\n"),
        case("json/json5", "SELECT json('{a:1, b:[0x10, .5, +1, Infinity], c:''s'', /* c */ d: \"e\",}');\nSELECT json_array_insert('[1,3]', '$[1]', 2);\n"),
        case("virtual-tables/generate-series", "SELECT * FROM generate_series(1, 10, 3);\nSELECT value FROM generate_series(5) LIMIT 3;\nSELECT sum(value) FROM generate_series(1, 100);\nSELECT * FROM generate_series(10, 1, -4);\n"),
        case("virtual-tables/pragma-functions", "SELECT name, narg FROM pragma_function_list WHERE name LIKE 'json_a%' ORDER BY 1, 2;\nSELECT * FROM pragma_collation_list ORDER BY name;\nSELECT name FROM pragma_module_list ORDER BY 1;\n"),
        case("virtual-tables/completion", "SELECT candidate FROM completion('SEL') ORDER BY 1;\nSELECT count(*) > 100 FROM completion('');\n"),
        case("virtual-tables/fsdir", "SELECT name, mode, length(data) FROM fsdir('d') ORDER BY name;\n", files={"d/a.txt": "abc", "d/b/c.txt": "hello"}),
        case("shell-extensions/decimal", "SELECT decimal('1.10'), decimal_add('0.1', '0.2'), decimal_sub('1', '0.001'), decimal_mul('1.5', '-2.25'), decimal_cmp('2', '10'), decimal_sum(x), decimal_exp('123.45'), decimal_pow2(-3) FROM (SELECT '0.1' x UNION ALL SELECT '0.2');\nSELECT x FROM (SELECT '10' x UNION ALL SELECT '9.5') ORDER BY x COLLATE decimal;\n"),
        case("shell-extensions/ieee754", "SELECT ieee754(47.49), ieee754(6683623321994527, -47), ieee754_mantissa(1.5), ieee754_exponent(1.5), hex(ieee754_to_blob(1.0)), ieee754_from_blob(x'3ff0000000000000'), ieee754_to_int(1.0), ieee754_from_int(4607182418800017408), ieee754_inc(1.0, 1);\n"),
        case("shell-extensions/hashes", "SELECT hex(sha3('abc')), hex(sha3('abc', 256)), hex(sha3('abc', 384)), sha1('abc'), hex(sha1b('abc')), hex(sha3_agg(x)), hex(sha3_query('SELECT 1')), sha1_query('SELECT 1') FROM (SELECT 'a' x UNION ALL SELECT 'b');\n"),
        case("shell-extensions/base64-base85", "SELECT base64(x'00ff10'), hex(base64('AP8Q')), base85(x'00ff10'), hex(base85(base85(x'0102'))), is_base85('abc'), base64('!!');\n"),
        case("shell-extensions/fileio", "SELECT writefile('out.txt', 'data');\nSELECT readfile('out.txt'), readfile('missing');\nSELECT lsmode(16877), lsmode(33188);\n"),
        case("shell-extensions/misc", "SELECT strtod('1.5e3'), dtostr(1.0/3), dtostr(1.0/3, 5), percentile IS NULL FROM (SELECT NULL percentile);\nSELECT shell_format_schema('CREATE TABLE t(a,b)', 1);\n"),
        case("dot-import/csv", ".import --csv data.csv t\nSELECT * FROM t;\nSELECT sql FROM sqlite_schema;\n.import --csv --skip 1 data.csv t\nSELECT count(*) FROM t;\n.mode tabs\n.import tab.txt t2\nSELECT * FROM t2;\n.import missing.csv t3\n", files={"data.csv": 'a,b,c\n1,"x,y",\n2,"q""uote",3\n', "tab.txt": "h1\th2\nv1\tv2\n"}),
        case("dot-import/schema-and-errors", "CREATE TABLE t(a, b);\n.import --csv data.csv t\nSELECT * FROM t;\n.import --csv data.csv\n.import\n", files={"data.csv": "1,2\n3\n4,5,6\n"}),
        case("dot-trace/trace", ".trace stdout\nSELECT 1;\nCREATE TABLE t(a);\n.trace off\nSELECT 2;\n"),
        case("cli-options/modes", TRICKY, ["-box"]),
        case("cli-options/table-markdown", "SELECT 1 AS a, 'x' AS b;\n.mode\n", ["-markdown", "-table"]),
        case("cli-options/separator-newline-nullvalue", "SELECT 1, NULL; SELECT 2, 3;\n", ["-separator", "::", "-newline", "!\n", "-nullvalue", "~"]),
        case("cli-options/echo-init", "SELECT 2;\n", ["-echo", "-init", "init.sql"], files={"init.sql": "SELECT 'init';\n.mode csv\n"}),
        case("cli-options/escape", "SELECT 'a' || char(7) || 'b';\n", ["-escape", "ascii"]),
        case("cli-options/quote-tabs-ascii-html-line-list-column", "SELECT 1 AS a, 'x y' AS b;\n", ["-quote", "-tabs", "-ascii", "-html", "-line", "-list", "-column"]),
        case("cli-options/readonly-memory", "CREATE TABLE t(a);\n", ["-readonly"]),
        case("cli-options/ifexists", "SELECT 1;\n", ["-ifexists", "missing.db"]),
        case("cli-options/deserialize", "SELECT * FROM t;\n", ["-deserialize", "fixture.db"]),
        case("cli-options/screenwidth", ".mode box --wordwrap on\nSELECT 'a long text that needs wrapping at a narrow screen width' AS v;\n", ["-screenwidth", "30"]),
        case("dot-system/unsafe-shell", ".shell echo hello\n.system printf x\n"),
        case("dot-database/connection", ".connection\n.connection 1\nCREATE TABLE t(a);\n.connection\n.connection 0\n.tables\n.connection close 1\n"),
        case("integrity/corrupt-header", "SELECT * FROM sqlite_schema;\n", ["bad.db"], files={"bad.db": "SQLite format 3\0" + "x" * 84}),
        case("integrity/not-a-database", "SELECT 1;\n.tables\n", ["text.db"], files={"text.db": "plain text\n" * 20}),
        case("ddl/limits-and-errors", "CREATE TABLE t(" + ", ".join(f"c{i}" for i in range(2001)) + ");\nSELECT " + "(" * 1001 + "1" + ")" * 1001 + ";\nCREATE TABLE \"\"(a);\nCREATE TABLE [x y](\"a b\", `c`);\nSELECT * FROM [x y];\n"),
    ]


SESSIONS = [
    {"milestone": "core", "id": "rollback-journal/create-reopen", "steps": [{"args": ["t.db"], "stdin": DATA}, {"args": ["t.db", "SELECT count(*) FROM emp"]}, {"args": ["t.db"], "stdin": ".tables\n.schema dept\n"}]},
    {"milestone": "core", "id": "transactions/uncommitted-at-exit", "steps": [{"args": ["t.db"], "stdin": "CREATE TABLE t(a);\nBEGIN;\nINSERT INTO t VALUES(1);\n"}, {"args": ["t.db", "SELECT count(*) FROM t"]}]},
    {"milestone": "core", "id": "rollback-journal/hot-journal-absent", "steps": [{"args": ["t.db"], "stdin": "PRAGMA journal_mode;\nCREATE TABLE t(a);\nBEGIN;\nINSERT INTO t VALUES(1);\nCOMMIT;\n"}, {"args": ["t.db", "PRAGMA journal_mode=PERSIST", "INSERT INTO t VALUES(2)"]}, {"args": ["t.db", "PRAGMA journal_mode=TRUNCATE", "INSERT INTO t VALUES(3)", "SELECT * FROM t"]}]},
    {"milestone": "core", "id": "cli-options/bail-file", "steps": [{"args": ["-bail", "t.db"], "stdin": "CREATE TABLE t(a);\nINSERT INTO t VALUES(1);\nINSERT INTO nope VALUES(1);\nINSERT INTO t VALUES(2);\n"}, {"args": ["t.db", "SELECT * FROM t"]}]},
    {"milestone": "core", "id": "dot-read/nested", "files": {"a.sql": encode(".read b.sql\nSELECT 'a';\n"), "b.sql": encode("CREATE TABLE b(x);\nINSERT INTO b VALUES('b');\nSELECT * FROM b;\n")}, "steps": [{"args": ["t.db"], "stdin": ".read a.sql\n"}, {"args": ["t.db", "SELECT * FROM b"]}]},
    {"milestone": "core", "id": "file-format/existing-nondb", "files": {"x.db": encode("")}, "steps": [{"args": ["x.db", "CREATE TABLE t(a)", "INSERT INTO t VALUES(1)"]}, {"args": ["x.db", "SELECT * FROM t"]}]},
    {"milestone": "extended", "id": "dot-output/output-and-once", "steps": [{"args": [":memory:"], "stdin": ".output out.txt\nSELECT 1;\n.print printed\n.output\nSELECT 2;\n.once once.txt\nSELECT 3;\nSELECT 4;\n.mode csv\n.output app.csv\nSELECT 'a', 'b';\n.output stdout\n"}]},
    {"milestone": "extended", "id": "dot-database/backup-restore-save-clone", "steps": [{"args": ["t.db"], "stdin": DATA + ".backup b.db\n.save s.db\n.clone c.db\n"}, {"args": [":memory:"], "stdin": ".restore b.db\nSELECT count(*) FROM emp;\n.open s.db\nSELECT count(*) FROM dept;\n.open c.db\n.tables\n.open --new n.db\n.tables\n"}]},
    {"milestone": "extended", "id": "dot-dump/round-trip", "steps": [{"args": ["t.db"], "stdin": DATA + "CREATE VIEW v AS SELECT 1;\nCREATE INDEX ix ON emp(name);\n.output dump.sql\n.dump\n.output\n"}, {"args": ["copy.db"], "stdin": ".read dump.sql\n.dump\n"}]},
    {"milestone": "extended", "id": "dot-import/new-table-file", "files": {"in.csv": encode("id,name\n1,ann\n2,\"b, c\"\n")}, "steps": [{"args": ["t.db"], "stdin": ".import --csv in.csv people\n"}, {"args": ["-header", "-column", "t.db", "SELECT * FROM people"]}]},
    {"milestone": "extended", "id": "maintenance/vacuum-into-attach", "steps": [{"args": ["t.db"], "stdin": DATA + "DELETE FROM emp WHERE id > 2;\nVACUUM INTO 'v.db';\nATTACH 'v.db' AS v;\nSELECT count(*) FROM v.emp;\n.databases\n"}]},
    {"milestone": "extended", "id": "dot-database/open-options", "steps": [{"args": [":memory:"], "stdin": ".open t.db\nCREATE TABLE t(a);\n.open --readonly t.db\nINSERT INTO t VALUES(1);\n.open --new t.db\n.tables\n.open --deserialize t.db\n.databases\n"}]},
    {"milestone": "complete", "id": "wal/mode-and-checkpoint", "steps": [{"args": ["w.db"], "stdin": "PRAGMA journal_mode=WAL;\nCREATE TABLE t(a);\nINSERT INTO t VALUES(1),(2);\nPRAGMA wal_checkpoint;\n"}, {"args": ["w.db", "PRAGMA journal_mode", "SELECT count(*) FROM t"]}, {"args": ["w.db", "PRAGMA journal_mode=DELETE", "SELECT * FROM t"]}]},
    {"milestone": "complete", "id": "wal/autocheckpoint", "steps": [{"args": ["w.db"], "stdin": "PRAGMA journal_mode=WAL;\nPRAGMA wal_autocheckpoint=10;\nCREATE TABLE t(a);\nWITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM c WHERE n<3000) INSERT INTO t SELECT 'r' || n FROM c;\nSELECT count(*) FROM t;\n"}, {"args": ["w.db", "PRAGMA integrity_check"]}]},
    {"milestone": "complete", "id": "shell-extensions/fileio-write", "steps": [{"args": [":memory:"], "stdin": "SELECT writefile('a.bin', x'000102');\nSELECT writefile('dir', NULL, 16877);\nSELECT writefile('dir/b.txt', 'b');\nSELECT name, length(data) FROM fsdir('dir') ORDER BY 1;\n"}]},
    {"milestone": "complete", "id": "file-format/page-size-autovacuum-encoding", "steps": [{"args": ["p.db"], "stdin": "PRAGMA page_size=1024;\nPRAGMA auto_vacuum=FULL;\nPRAGMA encoding='UTF-16le';\nCREATE TABLE t(a);\nINSERT INTO t VALUES('\u00e9t\u00e9');\n"}, {"args": ["p.db", "PRAGMA page_size", "PRAGMA auto_vacuum", "PRAGMA encoding", "SELECT * FROM t", "PRAGMA page_count"]}]},
]

CROSSREAD = [
    {"id": "file-format/basic", "write": DATA, "read": "SELECT * FROM emp;\nSELECT * FROM dept;\n"},
    {"id": "file-format/many-rows-and-overflow", "write": "CREATE TABLE big(id INTEGER PRIMARY KEY, t TEXT, b BLOB);\nWITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM c WHERE n<5000) INSERT INTO big SELECT n, printf('row-%08d', n), zeroblob(n % 7 * 300) FROM c;\nINSERT INTO big VALUES(-1, replace(hex(zeroblob(20000)), '0', 'z'), x'00ff');\n", "read": "SELECT count(*), sum(length(t)), sum(length(b)), min(id), max(id) FROM big;\nSELECT id, t FROM big WHERE id % 997 = 0;\n"},
    {"id": "file-format/indexes-and-deletes", "write": DATA + "CREATE INDEX ix ON emp(name, salary);\nCREATE UNIQUE INDEX ux ON dept(budget);\nWITH RECURSIVE c(n) AS (SELECT 100 UNION ALL SELECT n+1 FROM c WHERE n<3000) INSERT INTO emp(id, name, salary) SELECT n, 'n' || n, n FROM c;\nDELETE FROM emp WHERE id % 3 = 0;\n", "read": "SELECT count(*), sum(salary) FROM emp INDEXED BY ix WHERE name > 'n2';\nSELECT * FROM dept ORDER BY budget;\nPRAGMA freelist_count;\n"},
    {"id": "file-format/without-rowid-and-types", "write": "CREATE TABLE w(k TEXT PRIMARY KEY, v) WITHOUT ROWID;\nINSERT INTO w VALUES('a', 1), ('b', 2.5), ('c', NULL), ('d', x'abcd'), ('e', 'text'), ('f', 9223372036854775807), ('g', -9223372036854775808), ('h', 0), ('i', 1), ('j', 255), ('k', 65536), ('l', 1e308);\n", "read": "SELECT k, typeof(v), quote(v) FROM w;\n"},
    {"id": "file-format/schema-objects", "write": DATA + "CREATE VIEW v AS SELECT name FROM emp;\nCREATE TRIGGER tr AFTER INSERT ON emp BEGIN SELECT 1; END;\nCREATE TABLE seq(id INTEGER PRIMARY KEY AUTOINCREMENT);\nINSERT INTO seq DEFAULT VALUES;\nPRAGMA user_version=42;\nPRAGMA application_id=7;\n", "read": "SELECT type, name, tbl_name, sql FROM sqlite_schema ORDER BY name;\nSELECT * FROM v;\nPRAGMA user_version;\nPRAGMA application_id;\nSELECT * FROM sqlite_sequence;\n"},
    {"id": "file-format/page-size-512-autovacuum", "write": "PRAGMA page_size=512;\nPRAGMA auto_vacuum=INCREMENTAL;\n" + DATA + "DELETE FROM emp;\nPRAGMA incremental_vacuum(2);\n", "read": "PRAGMA page_size;\nPRAGMA auto_vacuum;\nSELECT * FROM dept;\n"},
    {"id": "file-format/utf16be", "write": "PRAGMA encoding='UTF-16be';\nCREATE TABLE t(a TEXT);\nINSERT INTO t VALUES('caf\u00e9'), ('\u4e2d\u6587'), ('');\n", "read": "PRAGMA encoding;\nSELECT a, length(a), hex(a) FROM t;\n"},
    {"id": "file-format/vacuum", "write": DATA + "DELETE FROM emp WHERE id < 5;\nVACUUM;\n", "read": "SELECT * FROM emp;\nPRAGMA page_count;\n"},
    {"id": "wal/checkpointed", "write": "PRAGMA journal_mode=WAL;\n" + DATA, "read": "PRAGMA journal_mode;\nSELECT * FROM emp;\n"},
    {"id": "file-format/analyze-stat", "write": DATA + "CREATE INDEX ix ON emp(dept);\nANALYZE;\n", "read": "SELECT * FROM sqlite_stat1 ORDER BY tbl, idx;\n"},
]
