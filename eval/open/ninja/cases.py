"""Define the multi-step Ninja scenarios of each milestone."""

import random

from runner import BASE


def case(identity, files, *steps):
    return {"id": identity, "files": files, "steps": list(steps)}


def step(*args, **extra):
    return {"args": list(args), **extra}


CHAIN = """rule cp
  command = cp $in $out
  description = CP $out
rule cat
  command = cat $in > $out
build mid1: cp src1
build mid2: cp src2
build out: cat mid1 mid2
build extra: cp src3
default out
"""
SOURCES = {"src1": "one\n", "src2": "two\n", "src3": "three\n"}

FAILING = """rule run
  command = $cmd
build ok1: run
  cmd = touch ok1
build bad1: run
  cmd = echo bad1 output; echo bad1 error >&2; exit 3
build after: run bad1
  cmd = touch after
build ok2: run
  cmd = touch ok2
build bad2: run
  cmd = exit 1
build ok3: run ok2
  cmd = touch ok3
build all: phony ok1 bad1 after ok2 bad2 ok3
default all
"""

DEPS = """rule cc
  command = printf '%s: %s hdr.h sub/inner.h\\n' $out $in > $out.d && cp $in $out
  deps = gcc
  depfile = $out.d
  description = CC $out
rule link
  command = cat $in > $out
build a.o: cc a.c
build b.o: cc b.c
build app: link a.o b.o
"""
DEPS_FILES = {"a.c": "a\n", "b.c": "b\n", "hdr.h": "h\n", "sub/inner.h": "i\n"}

LANGUAGE = """# A comment line.
ninja_required_version = 1.3
top = top-level
flags = -O1
rule show
  command = echo $flags [$in] [$out] [$top] $extra > $out
  description = SHOW $out ($flags)
rule lines
  command = cat $out.rsp > $out
  rspfile = $out.rsp
  rspfile_content = $in_newline
rule escape
  command = echo $$HOME-$:-$ $
      continued > $out
build out1: show in1 in2
  flags = -O2 $flags
  extra = local
build out$ two: show in1 | imp1 || oo1
build out3 out4 | out5: show in2 |@ out1
build lines.txt: lines in1 in2 out$ two
build esc: escape
include inc.ninja
subninja sub.ninja
build oo1: show
default out1 out$ two lines.txt esc incout subout
"""
LANGUAGE_FILES = {"in1": "1\n", "in2": "2\n", "imp1": "i\n", "inc.ninja": "flags = -O3\nbuild incout: show in1\n", "sub.ninja": "flags = -Os\ntop = shadow\nrule subrule\n  command = echo sub $top > $out\nbuild subout: subrule in2\n"}

ERRORS = {
    "missing-command": "rule r\nbuild a: r\n",
    "unknown-rule": "build a: nope b\n",
    "bad-indent": "rule r\n  command = x\n    depth = 2\n  extra = y\n",
    "bad-escape": "rule r\n  command = echo $\nbuild a: r $!\n",
    "duplicate-rule": "rule r\n  command = a\nrule r\n  command = b\n",
    "duplicate-build": "rule r\n  command = touch $out\nbuild a: r\nbuild a: r\n",
    "cycle": "rule r\n  command = touch $out\nbuild a: r b\nbuild b: r c\nbuild c: r a\n",
    "self-cycle": "rule r\n  command = touch $out\nbuild a: r a\n",
    "phony-cycle": "build a: phony a\n",
    "missing-input": "rule r\n  command = touch $out\nbuild a: r missing.c\n",
    "missing-nested": "rule r\n  command = touch $out\nbuild a: r b\nbuild b: r gone.h\n",
    "required-version": "ninja_required_version = 99.0\n",
    "old-required-version": "ninja_required_version = 1.0\nrule r\n  command = touch $out\nbuild a: r\n",
    "unknown-pool": "rule r\n  command = x\n  pool = nowhere\nbuild a: r\n",
    "pool-depth": "pool p\n  depth = -1\n",
    "pool-missing-depth": "pool p\n",
    "unterminated": "rule r\n  command = x\nbuild a: r $\n",
    "colon": "rule r\n  command = x\nbuild a r\n",
    "include-missing": "include nothere.ninja\n",
    "subninja-missing": "subninja nothere.ninja\n",
    "unexpected-variable": "rule r\n  command = x\n  bogus = 1\n",
    "empty-path": "rule r\n  command = x\nbuild $empty: r\n",
    "default-unknown": "default nothere\n",
    "tabs": "rule r\n\tcommand = x\n",
    "crlf": "rule r\r\n  command = touch $out\r\nbuild a: r\r\n",
    "nul": "rule r\n  command = x\0\n",
    "dyndep-unknown": "rule r\n  command = x\n  dyndep = dd\nbuild a: r\n",
    "deps-unknown": "rule r\n  command = touch $out\n  deps = bogus\n  depfile = a.d\nbuild a: r\n",
}

RESTAT = """rule maybe
  command = cmp -s $in $out || cp $in $out
  restat = 1
  description = MAYBE $out
rule cp
  command = cp $in $out
  description = CP $out
build gen.h: maybe gen.in
build obj: cp gen.h
build final: cp obj
"""

GENERATOR = """rule regen
  command = cp gen.txt build.ninja
  generator = 1
  description = REGEN $out
rule cp
  command = cp $in $out
build build.ninja: regen gen.txt
build one: cp src1
"""
GENERATOR_NEXT = GENERATOR.replace("build one: cp src1\n", "build one: cp src1\nbuild two: cp src2\n")

EDGES = """rule cp
  command = cp $in $out
  description = CP $out
rule stamp
  command = touch $out
  description = STAMP $out
build gen: stamp
build out | out.extra: cp src1 | imp || gen
  command = cp $in $out && touch out.extra
build check: stamp src2
build valid: cp src3 |@ check
build alias: phony out
build always: phony
build forced: cp src3 | always
build existing: phony
build uses-existing: cp src2 | existing
"""
EDGES = EDGES.replace("build out | out.extra: cp src1 | imp || gen\n  command = cp $in $out && touch out.extra\n", "rule cp2\n  command = cp $in $out && touch out.extra\n  description = CP2 $out\nbuild out | out.extra: cp2 src1 | imp || gen\n")

POOLS = """pool one
  depth = 1
pool two
  depth = 2
rule slow
  command = sleep 0.$delay && touch $out && echo $out
  pool = one
rule fast
  command = sleep 0.$delay && touch $out && echo $out
rule console
  command = touch $out && echo console $out
  pool = console
build a: slow
  delay = 4
build b: slow
  delay = 1
build c: fast
  pool = two
  delay = 0
build d: fast
  pool = two
  delay = 15
build e: console a b
build all: phony a b c d e
default all
"""

DYNDEP = """rule gen
  command = printf 'ninja_dyndep_version = 1\\nbuild out | out.imp: dyndep | dyn.in\\n' > $out
rule build
  command = cat dyn.in > $out && touch out.imp
  dyndep = out.dd
build out.dd: gen
build out: build || out.dd
rule cat2
  command = cat $in > $out
build user: cat2 out
"""

REGEN_LOOP = """rule regen
  command = touch $out
  generator = 1
build build.ninja: regen always
build always: phony
"""


def graph(seed=7, count=60):
    """Generate a seeded random DAG manifest and its source files."""
    rng = random.Random(seed)
    lines = ["rule cc\n  command = cat $in > $out\n  description = CC $out\n"]
    files, nodes = {}, []
    for index in range(count):
        inputs = rng.sample(nodes, min(len(nodes), rng.randint(0, 3)))
        if not inputs or rng.random() < 0.3:
            source = f"src/s{index}.c"
            files[source] = f"source {index}\n"
            inputs.append(source)
        order = f" || {rng.choice(nodes)}" if nodes and rng.random() < 0.1 else ""
        lines.append(f"build obj/n{index}.o: cc {' '.join(inputs)}{order}\n")
        nodes.append(f"obj/n{index}.o")
    lines.append(f"build all: phony {' '.join(nodes[-10:])}\ndefault all\n")
    files["build.ninja"] = "".join(lines)
    return files, sorted(name for name in files if name.startswith("src/"))


def core():
    big, sources = graph()
    return [
        case("incremental/chain-lifecycle", {"build.ninja": CHAIN, **SOURCES},
             step("-j1"), step("-j1"), step("-j1", touch=["src1"]), step("-j1"),
             step("-j1", remove=["mid2"]), step("-j1", write={"src2": "changed\n"}), step("-n", "-j1", touch=["src2"]),
             step("-j1"), step("-j1", "extra"), step("-j1", "out", "extra"), step("-t", "clean"), step("-j1", "out")),
        case("command-change/rule-edit", {"build.ninja": CHAIN, **SOURCES},
             step("-j1"), step("-j1", "-d", "explain", write={"build.ninja": CHAIN.replace("cat $in > $out", "cat $in $in > $out")}),
             step("-j1", "-d", "explain", write={"build.ninja": CHAIN.replace("cat $in > $out", "cat $in $in > $out").replace("CP $out", "COPY $out")}),
             step("-j1", "-v", touch=["src1"]), step("-j1", "--verbose", touch=["src3"], merge=True)),
        case("incremental/explicit-mtimes", {"build.ninja": CHAIN, **SOURCES, "mid1": "old\n"},
             step("-j1", "-d", "explain", "mid1", mtime={"mid1": BASE - 100}), step("-j1", "-d", "explain", "mid1", mtime={"src1": BASE + 1000}),
             step("-j1", "-d", "explain", "mid1", mtime={"src1": BASE + 2000, "mid1": BASE + 3000}), step("-j1", "-d", "explain", "mid1", mtime={"src1": BASE + 4000})),
        case("targets/selection", {"build.ninja": CHAIN, **SOURCES},
             step("-j1", "src1^"), step("-j1", "mid1^"), step("-j1", "ou"), step("-j1", "nothing"), step("-j1", "src1"), step("-j1", "missing^"),
             step("-j1", "./mid2"), step("-j1", "sub/../extra"), step("-j1", "out", "out")),
        case("keep-going/failures", {"build.ninja": FAILING},
             step("-j1"), step("-j1", "-k", "0"), step("-j1", "-k", "2"), step("-j1", "-k", "0", "-n"), step("-j1", "-k", "1", "ok3"), step("-j1", "-k", "-1"),
             step("-j1", "-k", "0", merge=True), step("-j1", "-k", "x"), step("-j1", "bad2", "--quiet")),
        case("options/flags", {"build.ninja": CHAIN, **SOURCES, "sub/build.ninja": "rule t\n  command = touch $out\nbuild here: t\n", "other.ninja": "rule t\n  command = echo other > $out\nbuild o: t\n"},
             step("-C", "sub"), step("-C", "sub"), step("-f", "other.ninja"), step("-f", "other.ninja", "-t", "targets"), step("-Csub", "-v", "-t", "clean"),
             step("-C", "nowhere"), step("-f", "missing.ninja"), step("--version"), step("-j3", "-h"), step("-h"), step("--help", "-j3"), step("-j3", "-x"),
             step("-j", "abc"), step("-j", "-2"), step("-l", "abc"), step("-l", "100", "-j1"), step("-j0", "--quiet"), step("-d", "list"), step("-d", "bogus"),
             step("-w", "list"), step("-w", "bogus"), step("-w", "phonycycle=warn", "-n"), step("-t", "list"), step("-t", "bogus"), step("-t"), step("-j"),
             step("--quiet", "-t", "clean"), step("-n", "-v", "-j1"), step("-j1", "-v", "--quiet")),
        case("manifest-language/syntax", {"build.ninja": LANGUAGE, **LANGUAGE_FILES},
             step("-n", "-v", "-j1"), step("-j1", "-v"), step("-j1"), step("-t", "commands"), step("-t", "targets", "all"), step("-t", "query", "out3", "out$ two", "out two")),
        *[case(f"manifest-errors/{name}", {"build.ninja": text}, step("-j1"), step("-j1", "-t", "targets")) for name, text in ERRORS.items()],
        case("warnings/dupbuild", {"build.ninja": ERRORS["duplicate-build"]}, step("-w", "dupbuild=warn", "-j1"), step("-w", "dupbuild=err", "-j1")),
        case("incremental/generated-graph", big,
             step("-j1"), step("-j1"), step("-j1", touch=sources[::7]), step("-j1", remove=["obj/n3.o", "obj/n17.o"]), step("-j1", "-n", touch=sources[1::5]),
             step("-t", "targets", "all"), step("-t", "commands", "obj/n59.o"), step("-t", "clean", "obj/n40.o"), step("-j1", "obj/n40.o")),
    ]


def extended():
    return [
        case("deps-log/gcc", {"build.ninja": DEPS, **DEPS_FILES},
             step("-j1"), step("-j1"), step("-t", "deps"), step("-j1", "-d", "explain", touch=["sub/inner.h"]), step("-j1"),
             step("-j1", "-d", "explain", remove=["hdr.h"]), step("-t", "deps", "a.o"), step("-t", "recompact"), step("-t", "deps"),
             step("-t", "missingdeps"), step("-j1", "-d", "keepdepfile", touch=["a.c"]), step("-t", "query", "a.o", "hdr.h")),
        case("depfile/plain", {"build.ninja": DEPS.replace("  deps = gcc\n", ""), **DEPS_FILES},
             step("-j1"), step("-j1"), step("-j1", touch=["hdr.h"]), step("-j1", write={"a.o.d": "a.o: a.c other.h\n"}), step("-j1", "-d", "explain", remove=["b.o.d"]), step("-t", "deps")),
        case("depfile/broken", {"build.ninja": DEPS.replace("$out $in hdr.h", "wrong.o $in hdr.h", 1).replace("printf", "printf", 1), **DEPS_FILES},
             step("-j1"), step("-j1", write={"build.ninja": DEPS.replace("printf '%s: %s hdr.h sub/inner.h\\n' $out $in > $out.d && ", "")}),
             step("-j1", write={"build.ninja": DEPS.replace("hdr.h sub/inner.h\\n'", "hdr.h \\\\\\n'")}, touch=["a.c", "b.c"])),
        case("restat/prune", {"build.ninja": RESTAT, "gen.in": "v1\n"},
             step("-j1"), step("-j1", "-d", "explain", touch=["gen.in"]), step("-j1"), step("-j1", "-v", write={"gen.in": "v2\n"}, touch=["gen.in"]),
             step("-j1", touch=["gen.in"]), step("-t", "restat"), step("-j1"), step("-t", "restat", "gen.h"), step("-j1", "-n", touch=["gen.in"])),
        case("generator/regen", {"build.ninja": GENERATOR, "gen.txt": GENERATOR, "src1": "1\n", "src2": "2\n"},
             step("-j1"), step("-j1", write={"gen.txt": GENERATOR_NEXT}, touch=["gen.txt"]), step("-j1"),
             step("-j1", write={"build.ninja": GENERATOR_NEXT.replace("cp gen.txt build.ninja", "cp gen.txt build.ninja && true")}),
             step("-t", "clean"), step("-t", "clean", "-g"), step("-j1", "-n", touch=["gen.txt"])),
        case("generator/loop", {"build.ninja": REGEN_LOOP}, step("-j1"), step("-j1", "-n")),
        case("edges/kinds", {"build.ninja": EDGES, "src1": "1\n", "src2": "2\n", "src3": "3\n", "imp": "i\n", "existing": "e\n"},
             step("-j1", "alias", "valid", "forced", "uses-existing"), step("-j1", "alias", "valid", "forced", "uses-existing"),
             step("-j1", "-d", "explain", "alias", touch=["gen"]), step("-j1", "-d", "explain", "alias", touch=["imp"]),
             step("-j1", "alias", remove=["out.extra"]), step("-j1", "alias", remove=["gen"]), step("-j1", "valid", touch=["src2"]),
             step("-j1", "uses-existing", remove=["existing"]), step("-t", "query", "out", "alias", "valid"), step("-t", "inputs", "alias", "valid")),
        case("pools/depth", {"build.ninja": POOLS},
             step("-j4"), step("-j4", "-t", "clean"), step("-j8", "--quiet"), step("-t", "clean"), step("-j1", env={"NINJA_STATUS": ""}),
             step("-n", "-j4", write={"build.ninja": POOLS.replace("depth = 2", "depth = 0")}, remove=["a", "b", "c", "d", "e"]), step("-n", write={"build.ninja": POOLS.replace("depth = 2", "depth = x")})),
        case("rspfile/lifecycle", {"build.ninja": LANGUAGE, **LANGUAGE_FILES},
             step("-j1", "lines.txt"), step("-j1", "-d", "keeprsp", "lines.txt", touch=["in1"]),
             step("-j1", "lines.txt", write={"build.ninja": LANGUAGE.replace("command = cat $out.rsp > $out", "command = cat $out.rsp > $out && exit 1")}, touch=["in1"])),
        case("builddir/logs", {"build.ninja": "builddir = state/dir\n" + CHAIN, **SOURCES},
             step("-j1"), step("-j1"), step("-j1", "-t", "recompact"), step("-j1", touch=["src2"]), step("-t", "cleandead"), step("-t", "restat")),
        case("dyndep/discovery", {"build.ninja": DYNDEP, "dyn.in": "d\n"},
             step("-j1"), step("-j1"), step("-j1", "-d", "explain", touch=["dyn.in"]), step("-j1", "user"), step("-t", "query", "out"),
             step("-j1", "-d", "explain", write={"out.dd": "ninja_dyndep_version = 2\n"}, touch=["out.dd"])),
        case("status/format", {"build.ninja": CHAIN, **SOURCES},
             step("-j1", env={"NINJA_STATUS": "[%s/%t/%f/%u/%r %p %%] "}), step("-t", "clean"), step("-j1", env={"NINJA_STATUS": "%z %o "}, merge=True),
             step("-t", "clean"), step("-j1", "--quiet", env={"NINJA_STATUS": "x "}), step("-t", "clean"), step("-j1", env={"CLICOLOR_FORCE": "1", "TERM": "xterm"})),
        case("status/color", {"build.ninja": "rule c\n  command = printf '\\033[31mred\\033[0m\\n'; printf 'err\\n' >&2\nbuild a: c\nbuild b: c\n"},
             step("-j1", "a"), step("-j1", "b", env={"CLICOLOR_FORCE": "1"}), step("-t", "clean"), step("-j1", "-v", env={"CLICOLOR_FORCE": "0"})),
        case("build-log/recovery", {"build.ninja": CHAIN, **SOURCES, ".ninja_log": "# ninja log v4\n0\t1\t2\tmid1\tcp src1 mid1\n"},
             step("-j1"), step("-j1", write={".ninja_log": "# ninja log v99\n"}), step("-j1", write={".ninja_log": "garbage\n"}),
             step("-j1", write={".ninja_log": "# ninja log v7\n1\t2\n3\t4\t5\tmid1\tzzzz\n\t\t\t\t\n"}), step("-j1", write={".ninja_deps": "# ninjadeps\n\x03\0\0\0"}),
             step("-j1", write={".ninja_deps": "garbage"}), step("-t", "recompact"), step("-t", "restat"), step("-j1")),
        case("deps-log/recovery", {"build.ninja": DEPS, **DEPS_FILES},
             step("-j1"), step("-j1", write={".ninja_deps": "# ninjadeps\n\x04\0\0\0\x08\0\0\0a.o\0\xff\xff\xff\xff\x40\0\0"}, touch=["a.c"]),
             step("-j1", write={".ninja_deps": "# ninjadeps\n\x01\0\0\0"}), step("-t", "deps"), step("-j1", "-d", "explain", touch=["hdr.h"])),
        case("interrupt/signals", {"build.ninja": "rule s\n  command = touch started && sleep 10\nbuild foo: s\nbuild bar: s\n"},
             step("-j1", "foo", signal=2, wait="started"), step("-j1", "bar", signal=15, wait="started", remove=["started"]),
             step("-j1", "foo", signal=1, wait="started", remove=["started"]), step("-t", "targets")),
        case("smart-terminal/status", {"build.ninja": CHAIN + "rule fail\n  command = echo failing output; exit 2\nbuild broken: fail\nrule long\n  command = touch $out\n  description = %s $out\nbuild long: long\n" % ("D" * 300), **SOURCES},
             step("-j1", tty=True), step("-j1", tty=True), step("-j1", "-v", tty=True, touch=["src1"]), step("-j1", "broken", tty=True), step("-j1", "long", tty=True),
             step("-t", "clean", tty=True), step("-j1", "--quiet", tty=True), step("-t", "clean"), step("-j1", tty=True, env={"TERM": "xterm"}), step("-j1", "broken", tty=True, env={"TERM": "xterm", "COLUMNS": "40"}), step("-t", "clean"), step("-j1", "long", tty=True, env={"TERM": "xterm"})),
        case("jobserver/makeflags", {"build.ninja": "rule p\n  command = echo [$$MAKEFLAGS]\nbuild a: p\n"},
             step("--quiet", env={"MAKEFLAGS": "-j4 --jobserver-auth=3,4"}, merge=True), step("--quiet", "-t", "clean"),
             step("--quiet", "-j2", env={"MAKEFLAGS": "-j4 --jobserver-auth=fifo:/nonexistent"}, merge=True), step("--quiet", "-t", "clean"),
             step("--quiet", env={"MAKEFLAGS": "-j4 --jobserver-fds=bogus"}, merge=True)),
    ]


TOOLS = """rule cc
  command = cc -c $in -o $out
  description = CC $out
rule link
  command = cc $in -o $out
  rspfile = $out.rsp
  rspfile_content = $in
rule gen
  command = touch $out
  generator = 1
build a.o: cc a.c | hdr.h
build b.o: cc b.c || order
build order: phony
build app: link a.o b.o
build lib/x.o: cc lib/x.c
build build.ninja: gen
build out$ with$ space: cc in$ space.c
default app
"""
TOOL_FILES = {"a.c": "", "b.c": "", "hdr.h": "", "lib/x.c": "", "in space.c": ""}
TOUCHER = "rule t\n  command = touch $out\nrule g\n  command = touch $out\n  generator = 1\nbuild a: t\nbuild b: t a\nbuild c: g\nbuild d: t b\n"


def complete():
    tool = lambda *args: step("-t", *args)
    return [
        case("tool-targets/basic", {"build.ninja": TOOLS, **TOOL_FILES},
             tool("targets"), tool("targets", "depth"), tool("targets", "depth", "1"), tool("targets", "depth", "0"), tool("targets", "rule"),
             tool("targets", "rule", "cc"), tool("targets", "rule", "phony"), tool("targets", "all"), tool("targets", "bogus"), tool("targets", "depth", "x"), tool("targets", "rule", "cc", "extra")),
        case("tool-commands/basic", {"build.ninja": TOOLS, **TOOL_FILES},
             tool("commands"), tool("commands", "app"), tool("commands", "-s", "app"), tool("commands", "a.o", "b.o"), tool("commands", "nothing"), tool("commands", "-h"), tool("commands", "-x")),
        case("tool-inputs/basic", {"build.ninja": TOOLS, **TOOL_FILES},
             tool("inputs"), tool("inputs", "app"), tool("inputs", "-d", "app"), tool("inputs", "-E", "out with space"), tool("inputs", "-0", "app"), tool("inputs", "--help"), tool("inputs", "nothing")),
        case("tool-multi-inputs/basic", {"build.ninja": TOOLS, **TOOL_FILES},
             tool("multi-inputs"), tool("multi-inputs", "app", "a.o"), tool("multi-inputs", "-d", "|", "app"), tool("multi-inputs", "--delimiter=::", "-0", "a.o"), tool("multi-inputs", "-h"), tool("multi-inputs", "bogus")),
        case("tool-query/basic", {"build.ninja": TOOLS, **TOOL_FILES},
             tool("query", "a.o"), tool("query", "app", "order", "a.c"), tool("query"), tool("query", "missing"), tool("query", "out with space")),
        case("tool-graph/basic", {"build.ninja": TOOLS, **TOOL_FILES}, tool("graph"), tool("graph", "app"), tool("graph", "a.o", "lib/x.o"), tool("graph", "missing")),
        case("tool-rules/basic", {"build.ninja": TOOLS + "rule unused\n  command = x\n  description = U $out\n", **TOOL_FILES}, tool("rules"), tool("rules", "-d"), tool("rules", "-h"), tool("rules", "extra")),
        case("tool-compdb/basic", {"build.ninja": TOOLS, **TOOL_FILES},
             tool("compdb"), tool("compdb", "cc"), tool("compdb", "-x", "link"), tool("compdb", "nothing"), tool("compdb", "-h"), tool("compdb", "-x", "cc", "link"),
             tool("compdb-targets", "app"), tool("compdb-targets", "-x", "app"), tool("compdb-targets", "a.c"), tool("compdb-targets"), tool("compdb-targets", "-h")),
        case("tool-clean/basic", {"build.ninja": TOUCHER},
             step("-j1"), tool("clean", "-n"), tool("clean", "b"), step("-j1"), tool("clean", "-r", "t"), step("-j1"), tool("clean", "-g"), tool("clean", "-r"),
             tool("clean", "-h"), tool("clean", "nothing"), step("-j1"), tool("clean", "-r", "nothing"), step("-v", "-t", "clean"), tool("clean")),
        case("tool-cleandead/basic", {"build.ninja": TOUCHER},
             step("-j1"), step("-t", "cleandead", write={"build.ninja": TOUCHER.replace("build d: t b\n", "")}), step("-j1"),
             step("-t", "cleandead", "-n", write={"build.ninja": TOUCHER.replace("build b: t a\n", "").replace("build d: t b\n", "build d: t a\n")}), tool("cleandead", "-h")),
        case("tool-restat/basic", {"build.ninja": TOUCHER},
             step("-j1"), tool("restat", "a"), step("-j1", touch=["a"]), tool("restat"), step("-j1", "-d", "explain"), tool("restat", "-h"), tool("restat", "nothing")),
        case("tool-recompact/basic", {"build.ninja": TOUCHER},
             tool("recompact"), step("-j1"), step("-j1", touch=["a"]), step("-j1", touch=["a"]), tool("recompact"), step("-j1"), step("-j1", write={"build.ninja": "rule t\n  command = touch $out\nbuild a: t\n"}), tool("recompact"), step("-j1")),
        case("tool-deps/basic", {"build.ninja": DEPS, **DEPS_FILES},
             tool("deps"), step("-j1"), tool("deps", "app"), tool("deps", "b.o", "a.o"), tool("deps", "missing"), step("-t", "deps", touch=["hdr.h"]), step("-t", "deps", remove=["b.o"])),
        case("tool-missingdeps/basic", {"build.ninja": DEPS.replace("hdr.h sub/inner.h", "gen.h") + "rule g\n  command = touch $out\nbuild gen.h: g\n", **DEPS_FILES},
             step("-j1", "gen.h"), step("-j1"), tool("missingdeps"), tool("missingdeps", "app"), tool("missingdeps", "a.o"), tool("missingdeps", "-h")),
        case("tool-urtle/basic", {"build.ninja": TOOLS, **TOOL_FILES}, tool("urtle"), tool("urtle", "extra"), step("-f", "missing.ninja", "-t", "urtle")),
        case("tool-browse/basic", {"build.ninja": TOOLS, **TOOL_FILES}, tool("browse"), tool("browse", "app"), tool("browse", "--help"), tool("browse", "--port=0", "--no-browser", "app")),
        case("tool-list/basic", {"build.ninja": TOOLS, **TOOL_FILES}, tool("list"), tool("list", "extra"), tool("msvc"), tool("wincodepage"), step("-ttargets"), step("-t", "commands", "-t", "list")),
        case("tools/broken-manifest", {"build.ninja": "rule r\n  command = x\nbuild a: nope\n"},
             tool("targets"), tool("recompact"), tool("restat"), tool("urtle"), tool("list"), tool("deps"), tool("clean")),
    ]


def milestones():
    return {"core": core(), "extended": extended(), "complete": complete()}
