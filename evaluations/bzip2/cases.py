"""Generate deterministic bzip2 evaluation cases."""

import base64
import bz2
import random

WORDS = b"the quick brown fox jumps over a lazy dog while block sorting huffman tables move to front runs".split()
SEPARATORS = (b" ", b" ", b" ", b"\n", b", ", b". ")


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


def noise(rng, size):
    return rng.randbytes(size)


def flip(data, rng):
    data = bytearray(data)
    data[rng.randrange(len(data))] ^= 1 << rng.randrange(8)
    return bytes(data)


def corruption(prefix, stream, rng, flips):
    """Return truncated, bit-flipped, and patched variants of one stream."""
    result = []
    for cut in sorted({1, 3, 4, 10, 14, len(stream) // 2, len(stream) - 10, len(stream) - 5, len(stream) - 1}):
        result.append(case(f"{prefix}-truncate-{cut}-d", ["-d"], stream[:cut]))
        result.append(case(f"{prefix}-truncate-{cut}-t", ["-t"], stream[:cut]))
    for number in range(flips):
        result.append(case(f"{prefix}-flip-{number}", (["-d"], ["-t"], ["-ds"])[number % 3], flip(stream, rng)))
    for name, offset in (("block-crc", 10), ("stream-crc", len(stream) - 2), ("block-magic", 4)):
        patched = bytearray(stream)
        patched[offset] ^= 0x55
        for args in (["-d"], ["-t"], ["-tvv"]):
            result.append(case(f"{prefix}-{name}{''.join(args)}", args, bytes(patched)))
    return result


def challenge():
    rng = random.Random(20261025)
    small = {
        "empty": b"",
        "byte": b"a",
        "newline": b"\n",
        "text-4k": text(rng, 4096),
        "noise-4k": noise(rng, 4096),
        "all-bytes": bytes(range(256)) * 16,
        "runs": b"".join(bytes([n % 256]) * n for n in range(1, 300)),
        "two-symbols": bytes(rng.choice(b"ab") for _ in range(5000)),
    }
    repetitive = {"zeros-64k": bytes(65536), "periodic-ab": b"ab" * 20000, "periodic-17": bytes(range(17)) * 4000}
    medium = text(rng, 250000)
    large = b"".join(text(rng, 50000) + noise(rng, 5000) + bytes(3000) for _ in range(20))
    result = []
    for name, data in small.items():
        for level in ("", "1", "9"):
            result.append(case(f"compress-{name}-{level or 'default'}", [f"-{level}"] if level else [], data))
    for name, data in repetitive.items():
        for args in (["-1"], ["-9"], ["--exponential"], ["-1", "--exponential"]):
            result.append(case(f"compress-{name}{''.join(args)}", args, data))
    for level in range(1, 10):
        result.append(case(f"compress-text-250k-{level}", [f"-{level}"], medium))
    result += [case("compress-mixed-1100k-9", ["-9"], large), case("compress-mixed-1100k-1", ["-1"], large)]
    for size in (99980, 99981, 99982, 99983):
        result.append(case(f"compress-block-boundary-{size}", ["-1"], noise(rng, size)))
    for size in (4, 5, 255, 256, 258, 259, 260, 261, 1000):
        result.append(case(f"compress-run-{size}", [], b"x" * size))
    result += [
        case("compress-small-mode", ["-s"], medium),
        case("compress-small-mode-1", ["-s1"], medium),
        case("compress-exponential-text", ["--exponential"], medium),
    ]
    for args in (["-v"], ["-vv"], ["-vvv"], ["-vvvv"], ["-vvvvv"]):
        result.append(case(f"verbose-compress{''.join(args)}", args, small["text-4k"]))
    result += [
        case("verbose-compress-empty", ["-v"], b""),
        case("verbose-compress-zeros", ["-vvvv"], repetitive["zeros-64k"]),
        case("verbose-compress-periodic", ["-vvvv", "--exponential"], repetitive["periodic-ab"]),
        case("verbose-compress-blocks", ["-1", "-vv"], medium),
    ]

    streams = {name: bz2.compress(data, 9) for name, data in {**small, **repetitive}.items()}
    streams["text-250k-1"] = bz2.compress(medium, 1)
    for name, stream in streams.items():
        for args in (["-d"], ["-ds"], ["-t"], ["-tv"]):
            result.append(case(f"decompress-{name}{''.join(args)}", args, stream))
    for args in (["-dv"], ["-dvv"], ["-dvvv"], ["-dvvvv"], ["-tvv"], ["-dsvv"]):
        result.append(case(f"verbose-decompress{''.join(args)}", args, streams["text-250k-1"]))

    first, second = streams["text-4k"], streams["runs"]
    empty = streams["empty"]
    tails = {
        "concatenated": first + second,
        "concatenated-empty": empty + first + empty,
        "garbage": first + b"garbage",
        "partial-magic": first + b"BZh9",
        "partial-stream": first + second[:20],
        "zero-tail": first + bytes(10),
    }
    for name, data in tails.items():
        for args in (["-d"], ["-dq"], ["-df"], ["-t"], ["-tq"], ["-tv"]):
            result.append(case(f"stream-{name}{''.join(args)}", args, data))
    for name, data in {"empty": b"", "plain": b"hello world\n", "short": b"B", "bz": b"BZ", "bzh": b"BZh", "level-0": b"BZh0" + first[4:], "level-a": b"BZha" + first[4:], "bad-z": b"BZx9" + first[4:], "lower": b"bZh9" + first[4:], "header-only": b"BZh9", "block-header": first[:10]}.items():
        for args in (["-d"], ["-df"], ["-dq"], ["-t"], ["-tv"], ["-dv"]):
            result.append(case(f"magic-{name}{''.join(args)}", args, data))
    oversized = bytearray(bz2.compress(medium, 9))
    oversized[3] = ord("1")
    result += [case("oversized-block-d", ["-d"], bytes(oversized)), case("oversized-block-t", ["-t"], bytes(oversized))]
    for number in range(5):
        result.append(case(f"random-body-{number}", ["-d"], b"BZh9" + noise(rng, 200)))
        result.append(case(f"random-block-{number}", ["-t"], b"BZh91AY&SY" + noise(rng, 200)))
    result += corruption("corrupt-text", first, rng, 45)
    result += corruption("corrupt-multiblock", bz2.compress(text(rng, 150000), 1), rng, 15)

    data = small["text-4k"]
    packed = streams["text-4k"]
    good = {"file": data, "other": small["noise-4k"]}
    named = {"a.bz2": packed, "b.bz2": second}
    damaged = {"good.bz2": packed, "crc.bz2": corruption("x", packed, random.Random(0), 0)[-3]["stdin_b64"], "trunc.bz2": packed[:-20], "plain": b"plain", "last.bz2": second}
    damaged["crc.bz2"] = base64.b64decode(damaged["crc.bz2"])
    files = [
        ("compress-file", ["file"], good),
        ("compress-keep", ["-k", "file"], good),
        ("compress-keep-long", ["--keep", "file"], good),
        ("compress-flag-after", ["file", "-k"], good),
        ("compress-two", ["file", "other"], good),
        ("compress-exists", ["file"], {**good, "file.bz2": b"old"}),
        ("compress-force", ["-f", "file"], {**good, "file.bz2": b"old"}),
        ("compress-force-long", ["--force", "file"], {**good, "file.bz2": b"old"}),
        ("compress-stdout", ["-c", "file"], good),
        ("compress-stdout-long", ["--stdout", "file"], good),
        ("compress-stdout-two", ["-c", "file", "other"], good),
        ("compress-verbose-files", ["-v", "file", "a-much-longer-file-name"], {"file": data, "a-much-longer-file-name": b"x" * 100}),
        ("compress-verbose-two", ["-vv", "-1", "file"], good),
        ("compress-empty-file", ["empty"], {"empty": b""}),
        ("compress-empty-verbose", ["-v", "empty"], {"empty": b""}),
        ("compress-space-name", ["space name"], {"space name": data}),
        ("compress-unicode-name", ["café"], {"café": data}),
        ("compress-nested", ["sub/file"], {"sub/file": data}),
        ("compress-dash-name", ["--", "-file"], {"-file": data}),
        ("compress-dash-flags", ["-k", "--", "-file", "-v"], {"-file": data, "-v": b"v"}),
        ("compress-dash-alone", ["-"], {}),
        ("compress-dash-stdout", ["-c", "-", "file"], good),
        ("compress-missing", ["missing"], {}),
        ("compress-missing-then-file", ["missing", "file"], good),
        ("compress-missing-stdout", ["-c", "missing"], {}),
        ("compress-directory", ["dir"], {"dir/x": b"x"}),
        ("compress-directory-stdout", ["-c", "dir"], {"dir/x": b"x"}),
        ("compress-output-directory", ["file"], {**good, "file.bz2/x": b"x"}),
        ("compress-output-directory-force", ["-f", "file"], {**good, "file.bz2/x": b"x"}),
        ("compress-long-name-1025", ["n" * 1025], {}),
        ("compress-long-name-1024", ["n" * 1024], {}),
        ("compress-long-name-300", ["n" * 300], {}),
        ("compress-small-file", ["-s", "file"], good),
        ("decompress-keep", ["-dk", "a.bz2"], named),
        ("decompress-two", ["-d", "a.bz2", "b.bz2"], named),
        ("decompress-stdout-two", ["-dc", "a.bz2", "b.bz2"], named),
        ("decompress-exists", ["-d", "a.bz2"], {**named, "a": b"old"}),
        ("decompress-force", ["-df", "a.bz2"], {**named, "a": b"old"}),
        ("decompress-not-bzip2", ["-d", "plain.bz2"], {"plain.bz2": b"plain"}),
        ("decompress-not-bzip2-force", ["-df", "plain.bz2"], {"plain.bz2": b"plain"}),
        ("decompress-not-bzip2-stdout-force", ["-dcf", "plain.bz2", "a.bz2"], {"plain.bz2": b"plain", **named}),
        ("decompress-not-bzip2-then-good", ["-d", "plain.bz2", "a.bz2"], {"plain.bz2": b"plain", **named}),
        ("decompress-crc-then-good", ["-d", "crc.bz2", "good.bz2"], damaged),
        ("decompress-crc-stdout", ["-dc", "crc.bz2", "good.bz2"], damaged),
        ("decompress-trunc-then-good", ["-d", "trunc.bz2", "good.bz2"], damaged),
        ("decompress-trunc-quiet", ["-dq", "trunc.bz2", "good.bz2"], damaged),
        ("decompress-empty-file", ["-d", "empty.bz2"], {"empty.bz2": b""}),
        ("decompress-missing", ["-d", "missing.bz2"], {}),
        ("decompress-missing-stdout", ["-dc", "missing.bz2"], {}),
        ("decompress-directory", ["-d", "dir.bz2"], {"dir.bz2/x": b"x"}),
        ("decompress-small-file", ["-ds", "a.bz2"], named),
        ("decompress-verbose-files", ["-dv", "a.bz2", "plain"], {"plain": b"plain", **named}),
        ("test-files", ["-t", "good.bz2", "crc.bz2", "trunc.bz2", "plain", "last.bz2"], damaged),
        ("test-files-verbose", ["-tv", "good.bz2", "crc.bz2", "trunc.bz2", "plain", "last.bz2"], damaged),
        ("test-files-quiet", ["-tq", "good.bz2", "crc.bz2", "trunc.bz2", "plain", "last.bz2"], damaged),
        ("test-good-long", ["--test", "good.bz2", "last.bz2"], damaged),
        ("test-missing", ["-t", "missing"], {}),
        ("test-directory", ["-t", "dir"], {"dir/x": b"x"}),
        ("test-stdout-conflict", ["-tc", "good.bz2"], damaged),
        ("test-stdout-conflict-long", ["--stdout", "--test"], {}),
    ]
    for suffix in (".bz2", ".bz", ".tbz2", ".tbz"):
        files.append((f"compress-suffix{suffix}", [f"a{suffix}"], {f"a{suffix}": packed}))
        files.append((f"compress-suffix-quiet{suffix}", ["-q", f"a{suffix}"], {f"a{suffix}": packed}))
        files.append((f"compress-suffix-force{suffix}", ["-cf", f"a{suffix}"], {f"a{suffix}": packed}))
    for name in ("a.bz2", "a.bz", "a.tbz2", "a.tbz", "a.gz", "a", ".bz2", "a.BZ2", "a.bz2.bz2", "a.tar.bz2"):
        files.append((f"decompress-name-{name}", ["-d", name], {name: packed}))
    files.append(("decompress-name-quiet", ["-dq", "a.gz"], {"a.gz": packed}))
    files.append(("decompress-name-out-exists", ["-d", "a.gz"], {"a.gz": packed, "a.gz.out": b"old"}))
    for identity, args, fixtures in files:
        result.append(case(identity, args, data, fixtures))

    stream = streams["text-4k"]
    for number, args in enumerate((
        ["-h"], ["--help"], ["-V"], ["-L"], ["--version"], ["--license"], ["-x"], ["-1x"], ["--foo"], ["---"],
        ["-hx"], ["-xh"], ["--help", "-x"], ["-V", "-x"], ["--repetitive-best"], ["--repetitive-fast"],
        ["--fast"], ["--best"], ["-91"], ["-19"], ["-zd"], ["-dz"], ["-q"], ["--quiet"], ["--compress"],
        ["--small"], ["--verbose"], ["--exponential", "-v"], ["-z", "--decompress", "-z"], ["-V", "-1"], ["-k"], ["-f"], ["-c"],
    )):
        result.append(case(f"options-{number}", args, data))
    for number, args in enumerate((["--decompress"], ["-dt"], ["-td"], ["-V", "-d"], ["-dq"], ["--decompress", "--small"], ["-z", "-d"], ["-cd"])):
        result.append(case(f"options-decompress-{number}", args, stream))
    for number, env in enumerate(({"BZIP2": "-1"}, {"BZIP": "-1"}, {"BZIP2": "-9", "BZIP": "-1"}, {"BZIP2": "  -v   -2  "}, {"BZIP2": "--bogus"}, {"BZIP2": ""}, {"BZIP2": "-1"}, {"BZIP2": "file"}, {"BZIP2": "-c"}, {"BZIP": "-d"})):
        args = ["-5"] if number == 6 else ["file"] if number == 8 else []
        result.append(case(f"env-{number}", args, stream if number == 9 else data, good, env))
    return result


def upstream(samples):
    """Return the upstream `make test` vectors, their expected outputs, and cases derived from the samples."""
    result, expected = [], {}
    for number, flags in ((1, "-1"), (2, "-2"), (3, "-3")):
        identity = f"make-test-compress-{number}"
        result.append(case(identity, [flags], samples[f"sample{number}.ref"]))
        expected[identity] = samples[f"sample{number}.bz2"]
    for number, flags in ((1, "-d"), (2, "-d"), (3, "-ds")):
        identity = f"make-test-decompress-{number}"
        result.append(case(identity, [flags], samples[f"sample{number}.bz2"]))
        expected[identity] = samples[f"sample{number}.ref"]
    for number in (1, 2, 3):
        ref, packed = samples[f"sample{number}.ref"], samples[f"sample{number}.bz2"]
        for level in range(1, 10):
            result.append(case(f"sample{number}-level-{level}", [f"-{level}"], ref))
        for args in (["-ds"], ["-t"], ["-tvv"], ["-dvvv"]):
            result.append(case(f"sample{number}{''.join(args)}", args, packed))
        result.append(case(f"sample{number}-file-compress", ["-k", "-v", f"sample{number}.ref"], files={f"sample{number}.ref": ref}))
        result.append(case(f"sample{number}-file-decompress", ["-d", f"sample{number}.bz2"], files={f"sample{number}.bz2": packed}))
    result += corruption("sample1", samples["sample1.bz2"], random.Random(1), 9)
    result += corruption("sample3", samples["sample3.bz2"], random.Random(3), 30)
    return result, expected
