"""Generate deterministic bzip2 evaluation cases.

Each case id is `<feature-id>/<case-name>`. The feature ids come from `grading.yaml`.
"""

import base64
import bz2
import itertools
import random

WORDS = b"the quick brown fox jumps over a lazy dog while block sorting huffman tables move to front runs".split()
SEPARATORS = (b" ", b" ", b" ", b"\n", b", ", b". ")
OPTIONS = {
    "-c": "stdout", "--stdout": "stdout", "-d": "decompress", "--decompress": "decompress", "-z": "compress", "--compress": "compress",
    "-k": "keep", "--keep": "keep", "-f": "force", "--force": "force", "-t": "test-integrity", "--test": "test-integrity",
    "-s": "small-mode", "--small": "small-mode", "-q": "quiet", "--quiet": "quiet", "-v": "verbose", "--verbose": "verbose",
    "-L": "license-version", "--license": "license-version", "-V": "license-version", "--version": "license-version",
    "-h": "help", "--help": "help", "--repetitive-best": "redundant-flags", "--repetitive-fast": "redundant-flags",
    "--exponential": "exponential", "--fast": "block-size", "--best": "block-size", "--": "end-of-options",
    **{f"-{level}": "block-size" for level in range(1, 10)},
}


def encode(data):
    return base64.b64encode(data).decode("ascii")


def case(identity, args, data=b"", files=None, env=None):
    item = {"id": identity, "args": args, "stdin_b64": encode(data)}
    if files:
        item["files"] = {name: encode(value) for name, value in files.items()}
    if env:
        item["env"] = env
    return item


def text(rng, size):
    out = bytearray()
    while len(out) < size:
        out += rng.choice(WORDS) + rng.choice(SEPARATORS)
    return bytes(out[:size])


def flip(data, rng):
    data = bytearray(data)
    data[rng.randrange(len(data))] ^= 1 << rng.randrange(8)
    return bytes(data)


def patch(data, offset):
    return data[:offset] + bytes([data[offset] ^ 0x55]) + data[offset + 1:]


def corruption(prefix, stream, rng, flips):
    """Return truncated, bit-flipped, and patched variants of one stream."""
    result = []
    for cut in sorted({1, 3, 4, 10, 14, len(stream) // 2, len(stream) - 10, len(stream) - 5, len(stream) - 1}):
        result.append(case(f"truncated-input/{prefix}-{cut}-d", ["-d"], stream[:cut]))
        result.append(case(f"truncated-input/{prefix}-{cut}-t", ["-t"], stream[:cut]))
    for number in range(flips):
        result.append(case(f"crc-check/{prefix}-flip-{number}", (["-d"], ["-t"], ["-ds"])[number % 3], flip(stream, rng)))
    for name, offset in (("block-crc", 10), ("stream-crc", len(stream) - 2), ("block-magic", 4)):
        for args in (["-d"], ["-t"], ["-tvv"]):
            result.append(case(f"crc-check/{prefix}-{name}{''.join(args)}", args, patch(stream, offset)))
    return result


def inputs(rng):
    return {
        "empty": b"",
        "byte": b"a",
        "newline": b"\n",
        "text-4k": text(rng, 4096),
        "noise-4k": rng.randbytes(4096),
        "all-bytes": bytes(range(256)) * 16,
        "runs": b"".join(bytes([n % 256]) * n for n in range(1, 300)),
        "two-symbols": bytes(rng.choice(b"ab") for _ in range(5000)),
    }


def challenge():
    """Return the replay cases per milestone and program name."""
    rng = random.Random(20261025)
    small = inputs(rng)
    repetitive = {"zeros-64k": bytes(65536), "periodic-ab": b"ab" * 20000, "periodic-17": bytes(range(17)) * 4000}
    medium = text(rng, 250000)
    large = b"".join(text(rng, 50000) + rng.randbytes(5000) + bytes(3000) for _ in range(20))
    core, extended, complete = [], [], []
    for name, data in small.items():
        for level in ("", "1", "9"):
            core.append(case(f"compress/{name}-{level or 'default'}", [f"-{level}"] if level else [], data))
    for name, data in repetitive.items():
        for args in (["-1"], ["-9"], ["--exponential"], ["-1", "--exponential"]):
            core.append(case(f"{'exponential' if '--exponential' in args else 'compress'}/{name}{''.join(args)}", args, data))
    for level in range(1, 10):
        core.append(case(f"block-size/text-250k-{level}", [f"-{level}"], medium))
    core += [case("block-size/mixed-1100k-9", ["-9"], large), case("block-size/mixed-1100k-1", ["-1"], large)]
    for size in (99980, 99981, 99982, 99983):
        core.append(case(f"block-size/boundary-{size}", ["-1"], rng.randbytes(size)))
    for size in (4, 5, 255, 256, 258, 259, 260, 261, 1000):
        core.append(case(f"compress/run-{size}", [], b"x" * size))
    core += [
        case("small-mode/compress", ["-s"], medium),
        case("small-mode/compress-1", ["-s1"], medium),
        case("exponential/text", ["--exponential"], medium),
    ]
    for args in (["-v"], ["-vv"], ["-vvv"], ["-vvvv"], ["-vvvvv"]):
        complete.append(case(f"verbose/compress{''.join(args)}", args, small["text-4k"]))
    complete += [
        case("verbose/compress-empty", ["-v"], b""),
        case("verbose/compress-zeros", ["-vvvv"], repetitive["zeros-64k"]),
        case("verbose/compress-periodic", ["-vvvv", "--exponential"], repetitive["periodic-ab"]),
        case("verbose/compress-blocks", ["-1", "-vv"], medium),
    ]

    streams = {name: bz2.compress(data, 9) for name, data in {**small, **repetitive}.items()}
    streams["text-250k-1"] = bz2.compress(medium, 1)
    for name, stream in streams.items():
        for args, feature in ((["-d"], "decompress"), (["-ds"], "small-mode"), (["-t"], "test-integrity"), (["-tv"], "test-integrity")):
            core.append(case(f"{feature}/{name}{''.join(args)}", args, stream))
    for args in (["-dv"], ["-dvv"], ["-dvvv"], ["-dvvvv"], ["-tvv"], ["-dsvv"]):
        complete.append(case(f"verbose/decompress{''.join(args)}", args, streams["text-250k-1"]))

    first, second, empty = streams["text-4k"], streams["runs"], streams["empty"]
    core.append(case("multiple-streams/decompress", ["-d"], first + second))
    tails = {
        "multiple-streams/concatenated": first + second,
        "multiple-streams/concatenated-empty": empty + first + empty,
        "trailing-garbage/garbage": first + b"garbage",
        "trailing-garbage/partial-magic": first + b"BZh9",
        "truncated-input/partial-stream": first + second[:20],
        "trailing-garbage/zero-tail": first + bytes(10),
    }
    for name, data in tails.items():
        for args in (["-d"], ["-dq"], ["-df"], ["-t"], ["-tq"], ["-tv"]):
            extended.append(case(f"{name}{''.join(args)}", args, data))
    magic = {"empty": b"", "plain": b"hello world\n", "short": b"B", "bz": b"BZ", "bzh": b"BZh", "level-0": b"BZh0" + first[4:], "level-a": b"BZha" + first[4:], "bad-z": b"BZx9" + first[4:], "lower": b"bZh9" + first[4:], "header-only": b"BZh9", "block-header": first[:10]}
    for name, data in magic.items():
        for args in (["-d"], ["-df"], ["-dq"], ["-t"], ["-tv"], ["-dv"]):
            extended.append(case(f"not-bzip2/{name}{''.join(args)}", args, data))
    oversized = b"BZh1" + bz2.compress(medium, 9)[4:]
    extended += [case("crc-check/oversized-block-d", ["-d"], oversized), case("crc-check/oversized-block-t", ["-t"], oversized)]
    for number in range(5):
        extended.append(case(f"crc-check/random-body-{number}", ["-d"], b"BZh9" + rng.randbytes(200)))
        extended.append(case(f"crc-check/random-block-{number}", ["-t"], b"BZh91AY&SY" + rng.randbytes(200)))
    extended += corruption("text", first, rng, 45)
    extended += corruption("multiblock", bz2.compress(text(rng, 150000), 1), rng, 15)

    data = small["text-4k"]
    good = {"file": data, "other": small["noise-4k"]}
    named = {"a.bz2": first, "b.bz2": second}
    damaged = {"good.bz2": first, "crc.bz2": patch(first, 10), "trunc.bz2": first[:-20], "plain": b"plain", "last.bz2": second}
    damaged_args = ["good.bz2", "crc.bz2", "trunc.bz2", "plain", "last.bz2"]
    files = [
        ("compress/file", ["file"], good),
        ("keep/compress", ["-k", "file"], good),
        ("keep/compress-long", ["--keep", "file"], good),
        ("keep/flag-after-file", ["file", "-k"], good),
        ("compress/two-files", ["file", "other"], good),
        ("force/compress-exists", ["file"], {**good, "file.bz2": b"old"}),
        ("force/compress", ["-f", "file"], {**good, "file.bz2": b"old"}),
        ("force/compress-long", ["--force", "file"], {**good, "file.bz2": b"old"}),
        ("stdout/compress", ["-c", "file"], good),
        ("stdout/compress-long", ["--stdout", "file"], good),
        ("stdout/compress-two", ["-c", "file", "other"], good),
        ("verbose/compress-files", ["-v", "file", "a-much-longer-file-name"], {"file": data, "a-much-longer-file-name": b"x" * 100}),
        ("verbose/compress-file-vv", ["-vv", "-1", "file"], good),
        ("compress/empty-file", ["empty"], {"empty": b""}),
        ("verbose/compress-empty-file", ["-v", "empty"], {"empty": b""}),
        ("compress/space-name", ["space name"], {"space name": data}),
        ("compress/unicode-name", ["café"], {"café": data}),
        ("compress/nested", ["sub/file"], {"sub/file": data}),
        ("end-of-options/dash-name", ["--", "-file"], {"-file": data}),
        ("end-of-options/dash-flags", ["-k", "--", "-file", "-v"], {"-file": data, "-v": b"v"}),
        ("end-of-options/dash-alone", ["-"], {}),
        ("end-of-options/dash-stdout", ["-c", "-", "file"], good),
        ("exit-status/compress-missing", ["missing"], {}),
        ("exit-status/compress-missing-then-file", ["missing", "file"], good),
        ("exit-status/compress-missing-stdout", ["-c", "missing"], {}),
        ("directory-input/compress", ["dir"], {"dir/x": b"x"}),
        ("directory-input/compress-stdout", ["-c", "dir"], {"dir/x": b"x"}),
        ("directory-input/compress-output", ["file"], {**good, "file.bz2/x": b"x"}),
        ("directory-input/compress-output-force", ["-f", "file"], {**good, "file.bz2/x": b"x"}),
        ("long-file-name/1025", ["n" * 1025], {}),
        ("long-file-name/1024", ["n" * 1024], {}),
        ("long-file-name/300", ["n" * 300], {}),
        ("small-mode/compress-file", ["-s", "file"], good),
        ("keep/decompress", ["-dk", "a.bz2"], named),
        ("decompress/two-files", ["-d", "a.bz2", "b.bz2"], named),
        ("stdout/decompress-two", ["-dc", "a.bz2", "b.bz2"], named),
        ("force/decompress-exists", ["-d", "a.bz2"], {**named, "a": b"old"}),
        ("force/decompress", ["-df", "a.bz2"], {**named, "a": b"old"}),
        ("not-bzip2/file", ["-d", "plain.bz2"], {"plain.bz2": b"plain"}),
        ("force/not-bzip2-file", ["-df", "plain.bz2"], {"plain.bz2": b"plain"}),
        ("force/not-bzip2-stdout", ["-dcf", "plain.bz2", "a.bz2"], {"plain.bz2": b"plain", **named}),
        ("not-bzip2/then-good", ["-d", "plain.bz2", "a.bz2"], {"plain.bz2": b"plain", **named}),
        ("crc-check/then-good", ["-d", "crc.bz2", "good.bz2"], damaged),
        ("crc-check/stdout", ["-dc", "crc.bz2", "good.bz2"], damaged),
        ("truncated-input/then-good", ["-d", "trunc.bz2", "good.bz2"], damaged),
        ("quiet/truncated", ["-dq", "trunc.bz2", "good.bz2"], damaged),
        ("truncated-input/empty-file", ["-d", "empty.bz2"], {"empty.bz2": b""}),
        ("exit-status/decompress-missing", ["-d", "missing.bz2"], {}),
        ("exit-status/decompress-missing-stdout", ["-dc", "missing.bz2"], {}),
        ("directory-input/decompress", ["-d", "dir.bz2"], {"dir.bz2/x": b"x"}),
        ("small-mode/decompress-file", ["-ds", "a.bz2"], named),
        ("verbose/decompress-files", ["-dv", "a.bz2", "plain"], {"plain": b"plain", **named}),
        ("test-integrity/files", ["-t", *damaged_args], damaged),
        ("verbose/test-files", ["-tv", *damaged_args], damaged),
        ("quiet/test-files", ["-tq", *damaged_args], damaged),
        ("test-integrity/good-long", ["--test", "good.bz2", "last.bz2"], damaged),
        ("exit-status/test-missing", ["-t", "missing"], {}),
        ("directory-input/test", ["-t", "dir"], {"dir/x": b"x"}),
        ("test-integrity/stdout-conflict", ["-tc", "good.bz2"], damaged),
        ("test-integrity/stdout-conflict-long", ["--stdout", "--test"], {}),
        ("output-name-guess/quiet", ["-dq", "a.gz"], {"a.gz": first}),
        ("output-name-guess/out-exists", ["-d", "a.gz"], {"a.gz": first, "a.gz.out": b"old"}),
    ]
    for suffix in (".bz2", ".bz", ".tbz2", ".tbz"):
        files.append((f"file-suffixes/compress{suffix}", [f"a{suffix}"], {f"a{suffix}": first}))
        files.append((f"file-suffixes/compress-quiet{suffix}", ["-q", f"a{suffix}"], {f"a{suffix}": first}))
        files.append((f"file-suffixes/compress-force{suffix}", ["-cf", f"a{suffix}"], {f"a{suffix}": first}))
    for name in ("a.bz2", "a.bz", "a.tbz2", "a.tbz", "a.gz", "a", ".bz2", "a.BZ2", "a.bz2.bz2", "a.tar.bz2"):
        files.append((f"{'file-suffixes' if '.bz' in name or '.tbz' in name else 'output-name-guess'}/decompress-{name}", ["-d", name], {name: first}))
    for identity, args, fixtures in files:
        extended.append(case(identity, args, data, fixtures))

    for args in (
        ["-h"], ["--help"], ["-V"], ["-L"], ["--version"], ["--license"], ["-x"], ["-1x"], ["--foo"], ["---"],
        ["-hx"], ["-xh"], ["--help", "-x"], ["-V", "-x"], ["--repetitive-best"], ["--repetitive-fast"],
        ["--fast"], ["--best"], ["-91"], ["-19"], ["-zd"], ["-dz"], ["-q"], ["--quiet"], ["--compress"],
        ["--small"], ["--verbose"], ["--exponential", "-v"], ["-z", "--decompress", "-z"], ["-V", "-1"], ["-k"], ["-f"], ["-c"],
    ):
        extended.append(case(f"{OPTIONS.get(args[0][:2] if args[0][1] != '-' else args[0], 'help')}/options{''.join(args)}", args, data))
    for args in (["--decompress"], ["-dt"], ["-td"], ["-V", "-d"], ["-dq"], ["--decompress", "--small"], ["-z", "-d"], ["-cd"]):
        extended.append(case(f"decompress/options{''.join(args)}", args, first))
    for number, env in enumerate(({"BZIP2": "-1"}, {"BZIP": "-1"}, {"BZIP2": "-9", "BZIP": "-1"}, {"BZIP2": "  -v   -2  "}, {"BZIP2": "--bogus"}, {"BZIP2": ""}, {"BZIP2": "-1"}, {"BZIP2": "file"}, {"BZIP2": "-c"}, {"BZIP": "-d"})):
        args = ["-5"] if number == 6 else ["file"] if number == 8 else []
        complete.append(case(f"environment/{number}", args, first if number == 9 else data, good, env))
    return {"replay-core": {"bzip2": core}, "replay-extended": {"bzip2": extended}, "replay-complete": {"bzip2": complete, **aliases(first, second, data)}}


def aliases(packed, second, data):
    """Return cases for the program names that select decompression or output to stdout."""
    files = {"a.bz2": packed, "b.bz2": second, "a": data, "plain": b"plain"}
    result = {}
    for name in ("bunzip2", "bzcat", "bz2cat", "BUNZIP2", "BZCAT"):
        result[name] = [
            case(f"program-name/{name}-stdin", [], packed),
            case(f"program-name/{name}-file", ["a.bz2"], files=files),
            case(f"program-name/{name}-two", ["a.bz2", "b.bz2"], files=files),
            case(f"program-name/{name}-guess", ["a"], files=files),
            case(f"program-name/{name}-plain", ["plain"], files=files),
            case(f"program-name/{name}-compress", ["-z"], data),
            case(f"program-name/{name}-compress-file", ["-z", "a"], files=files),
            case(f"program-name/{name}-test", ["-t", "a.bz2"], files=files),
            case(f"program-name/{name}-help", ["--help"]),
            case(f"program-name/{name}-bad-flag", ["-x"]),
        ]
    return result


def generate(count=400):
    """Return seeded probes over all option pairs, option sets, input formats, and file layouts."""
    rng = random.Random(4242)
    shorts = [option for option in OPTIONS if len(option) == 2 and option != "--"]
    longs = [option for option in OPTIONS if option.startswith("--")]
    raw = inputs(rng)
    formats = {**{f"raw-{name}": data for name, data in raw.items()}, "raw-text-40k": text(rng, 40000)}
    for name in ("text-4k", "runs", "noise-4k", "empty"):
        stream = bz2.compress(raw[name], rng.randint(1, 9))
        formats.update({f"bz2-{name}": stream, f"bz2-{name}-twice": stream + stream, f"bz2-{name}-garbage": stream + b"junk", f"bz2-{name}-truncated": stream[:-7], f"bz2-{name}-flipped": flip(stream, rng)})
    names = ["in", "in.bz2", "in.bz", "in.tbz2", "in.tbz", "in.gz", "-dash"]
    plans = [[f"-{a[1]}{b[1]}"] for a, b in itertools.combinations(shorts, 2)]
    pairs = len(plans)
    while len(plans) < pairs + count:
        options = rng.sample(shorts + longs, rng.randint(0, 4))
        clustered = [option for option in options if len(option) == 2]
        if len(clustered) > 1 and rng.random() < 0.5:
            options = [option for option in options if len(option) != 2] + ["-" + "".join(option[1] for option in clustered)]
        plans.append(options)
    result = []
    for number, options in enumerate(plans):
        format_name = rng.choice(sorted(formats))
        data = formats[format_name]
        layout = rng.choice(("stdin", "file", "file", "two-files", "existing-output", "end-of-options"))
        files, args, env = {}, list(options), None
        if layout == "stdin":
            pass
        elif layout == "end-of-options":
            files["-dash"] = data
            args += ["--", "-dash"]
        else:
            chosen = rng.sample(names[:-1], 2 if layout == "two-files" else 1)
            files.update({name: data for name in chosen})
            if layout == "existing-output":
                files[chosen[0][:-4] if chosen[0].endswith(".bz2") else chosen[0] + ".bz2"] = b"old"
            args += chosen
            rng.shuffle(args)
        if rng.random() < 0.1:
            env = {"BZIP2": rng.choice(["-1", "-v", "-q", "-k", "-s"])}
        flags = [token for token in options if token.startswith("-")]
        feature = OPTIONS.get(flags[0] if flags[0].startswith("--") else flags[0][:2], "compress") if flags else ("environment" if env else "compress")
        result.append(case(f"{feature}/generated-{number}-{layout}-{format_name}", args, data, files, env))
    return result


def upstream(samples):
    """Return the upstream `make test` vectors, their expected outputs, and cases derived from the sample files."""
    test, derived, expected = [], [], {}
    for number, flags in ((1, "-1"), (2, "-2"), (3, "-3")):
        identity = f"compress/make-test-sample{number}"
        test.append(case(identity, [flags], samples[f"sample{number}.ref"]))
        expected[identity] = samples[f"sample{number}.bz2"]
    for number, flags in ((1, "-d"), (2, "-d"), (3, "-ds")):
        identity = f"{'small-mode' if flags == '-ds' else 'decompress'}/make-test-sample{number}"
        test.append(case(identity, [flags], samples[f"sample{number}.bz2"]))
        expected[identity] = samples[f"sample{number}.ref"]
    for number in (1, 2, 3):
        ref, packed = samples[f"sample{number}.ref"], samples[f"sample{number}.bz2"]
        for level in range(1, 10):
            derived.append(case(f"block-size/sample{number}-{level}", [f"-{level}"], ref))
        for args, feature in ((["-ds"], "small-mode"), (["-t"], "test-integrity"), (["-tvv"], "verbose"), (["-dvvv"], "verbose")):
            derived.append(case(f"{feature}/sample{number}{''.join(args)}", args, packed))
        derived.append(case(f"keep/sample{number}-file", ["-k", "-v", f"sample{number}.ref"], files={f"sample{number}.ref": ref}))
        derived.append(case(f"file-suffixes/sample{number}-file", ["-d", f"sample{number}.bz2"], files={f"sample{number}.bz2": packed}))
    derived += corruption("sample1", samples["sample1.bz2"], random.Random(1), 9)
    derived += corruption("sample3", samples["sample3.bz2"], random.Random(3), 30)
    return {"upstream-tests": test, "upstream-samples": derived}, expected
