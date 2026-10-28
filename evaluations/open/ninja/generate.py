"""Generate seeded Ninja scenarios that combine manifest features, flags, tools, and state changes."""

import random

from cases import case, step

FLAGS = [["-v"], ["--verbose"], ["--quiet"], ["-k", "0"], ["-k", "2"], ["-d", "explain"], ["-d", "keepdepfile"], ["-d", "keeprsp"], ["-w", "phonycycle=warn"], ["-w", "phonycycle=err"], ["-l", "1000"]]
STATUS = ["[%f/%t] ", "%s|%t|%u|%r|%f %p%% ", "", "[%%] "]
TOOLS = [["targets"], ["targets", "all"], ["targets", "depth", "2"], ["targets", "rule", "copy"], ["commands"], ["commands", "-s", "{t}"], ["inputs", "{t}"], ["inputs", "-d", "-E", "{t}"],
         ["multi-inputs", "-d", ":", "{t}"], ["query", "{t}"], ["graph", "{t}"], ["rules", "-d"], ["compdb"], ["compdb", "-x", "copy"], ["compdb-targets", "{t}"], ["deps"], ["missingdeps"],
         ["clean"], ["clean", "-g"], ["clean", "-r", "copy"], ["clean", "{t}"], ["cleandead"], ["recompact"], ["restat"], ["restat", "{t}"], ["browse", "{t}"], ["urtle"], ["list"]]
RULES = {
    "copy": "  command = sort $in > $out\n",
    "concat": "  command = cat $in > $out\n  description = CAT $out\n",
    "stamp": "  command = touch $out\n  description = STAMP $out\n  restat = 1\n",
    "same": "  command = cat $in > $out.new && (cmp -s $out.new $out || mv $out.new $out); rm -f $out.new\n  restat = 1\n",
    "dep": "  command = printf '%s: %s hdr$hidx.h\\n' $out $in > $out.d && cat $in > $out\n  depfile = $out.d\n  deps = gcc\n",
    "plaindep": "  command = printf '%s: hdr$hidx.h\\n' $out > $out.d && cat $in > $out\n  depfile = $out.d\n",
    "rsp": "  command = cat $out.rsp > $out\n  rspfile = $out.rsp\n  rspfile_content = $in_newline\n",
    "fail": "  command = echo failing $out; exit $code\n",
    "noisy": "  command = echo out $out; echo err $out >&2; cat $in > $out\n",
    "gen": "  command = touch $out\n  generator = 1\n",
}


def manifest(rng):
    """Return a random valid manifest, its sources, and its outputs."""
    sources = [f"s{index}.c" for index in range(rng.randint(2, 5))]
    files = {name: f"{name}\n" for name in sources} | {f"hdr{index}.h": "h\n" for index in range(3)}
    lines = [f"rule {name}\n{body}" for name, body in RULES.items()]
    if rng.random() < 0.4:
        lines.insert(0, f"pool p\n  depth = {rng.randint(1, 3)}\n")
    if rng.random() < 0.2:
        lines.insert(0, "builddir = state\n")
    outputs = []
    for index in range(rng.randint(3, 9)):
        rule = rng.choice([name for name in RULES if name != "fail" or rng.random() < 0.3])
        output = f"o{index}" if rng.random() < 0.9 else f"o$ {index}"
        pool = rng.choice(["", "", "  pool = p\n" if "pool p" in lines[0] else "", "  pool = console\n"])
        inputs = rng.sample(sources + outputs, rng.randint(1, min(3, len(sources + outputs))))
        extra = (" | " + rng.choice(sources) if rng.random() < 0.2 else "") + (" || " + rng.choice(outputs) if outputs and rng.random() < 0.2 else "") + (" |@ " + rng.choice(outputs) if outputs and rng.random() < 0.1 else "")
        implicit = f" | o{index}.extra" if rule == "stamp" and rng.random() < 0.3 else ""
        lines.append(f"build {output}{implicit}: {rule} {' '.join(inputs)}{extra}\n  hidx = {rng.randint(0, 2)}\n  code = {rng.randint(1, 4)}\n{pool}")
        outputs.append(output)
    if rng.random() < 0.5:
        lines.append(f"build all: phony {' '.join(outputs)}\n")
        outputs.append("all")
    if rng.random() < 0.3:
        lines.append(f"default {' '.join(rng.sample(outputs, 2))}\n")
    files["build.ninja"] = "".join(lines)
    return files, sources, [name.replace("$ ", " ") for name in outputs]


def mutate(rng, text):
    """Damage a manifest with one random edit."""
    position = rng.randrange(len(text))
    edit = rng.choice(["delete", "insert", "swap", "line"])
    if edit == "delete":
        return text[:position] + text[position + rng.randint(1, 4):]
    if edit == "insert":
        return text[:position] + rng.choice(["$", ":", "|", "||", "\n", " ", "=", "\t", "rule", "build", "${", "$\n"]) + text[position:]
    if edit == "swap":
        lines = text.split("\n")
        index = rng.randrange(len(lines) - 1)
        lines[index], lines[index + 1] = lines[index + 1], lines[index]
        return "\n".join(lines)
    lines = text.split("\n")
    lines.insert(rng.randrange(len(lines)), rng.choice(lines))
    return "\n".join(lines)


def scenario(rng, index):
    files, sources, outputs = manifest(rng)
    target = rng.choice(outputs)
    steps = [step("-j1", *rng.choice(FLAGS), env={"NINJA_STATUS": rng.choice(STATUS)})]
    for _ in range(rng.randint(3, 7)):
        action = rng.choice(["touch", "remove", "command", "tool", "dry", "target", "flags", "noop"])
        args = ["-j1", *rng.choice(FLAGS)] if action in ("flags", "touch", "remove", "command") else ["-j1"]
        extra = {}
        if action == "touch":
            extra["touch"] = rng.sample(sources + ["hdr0.h", "hdr1.h"], 2)
        elif action == "remove":
            args += ["-k", "0"]
            extra["remove"] = [name for name in rng.sample(outputs, 2) if name != "all"]
        elif action == "command":
            files_next = files["build.ninja"].replace("sort $in > $out", "sort -r $in > $out") if rng.random() < 0.5 else files["build.ninja"].replace("CAT $out", "JOIN $out")
            extra["write"] = {"build.ninja": files_next}
        elif action == "tool":
            args = ["-t", *[part.replace("{t}", target) for part in rng.choice(TOOLS)]]
        elif action == "dry":
            args = ["-n", f"-j{rng.randint(1, 4)}", *rng.choice(FLAGS)]
        elif action == "target":
            args += [rng.choice([target, f"{rng.choice(sources)}^", target + "x"])]
        steps.append(step(*args, **extra))
    return case(f"{rng.choice(['incremental', 'manifest-language', 'options'])}/generated-{index}", files, *steps)


def broken(rng, index):
    files, _, _ = manifest(rng)
    files["build.ninja"] = mutate(rng, files["build.ninja"])
    return case(f"manifest-errors/generated-{index}", files, step("-n", "-j1"), step("-t", "targets", "all"))


def scenarios(seed=20261025, count=120, damaged=80):
    rng = random.Random(seed)
    return [scenario(rng, index) for index in range(count)] + [broken(rng, index) for index in range(damaged)]
