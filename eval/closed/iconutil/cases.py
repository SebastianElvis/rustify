"""Generate deterministic iconutil cases from images and containers that this module writes itself."""

import base64
from functools import lru_cache
import hashlib
from pathlib import Path
import random
import struct
import zlib

SIZES = (16, 32, 128, 256, 512)
SLOTS = tuple((size, scale) for size in SIZES for scale in (1, 2))
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
ADAM7 = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))
TABLES = [bytes((i + k) & 255 for i in range(256)) for k in range(256)]
# The reference reads these system asset catalogs. The macOS build in reference.yaml pins their bytes.
CATALOGS = {
    "glyph": ("/System/Library/CoreServices/WatchFaceAlert.app/Contents/Resources/Assets.car", "98856866c6603d546526433499c6b676bc435d11f792f12e9bec1f4eb5f58c63"),
    "iconset": ("/System/Library/CoreServices/Screen Time.app/Contents/Resources/Assets.car", "53aca68be1759f973e974637cf894caedff3464c0e3e5584b433ba6b0c4fc921"),
    "layered": ("/System/Library/CoreServices/Batteries.app/Contents/Resources/Assets.car", "429c144de24010cddb6c460d90f0e24852b4ce9e2ad8950258146c3e1164cbda"),
    "noicon": ("/System/Library/CoreServices/iCloud.app/Contents/Resources/Assets.car", "0b1f69c5cb69f24a09fe6a13facaaa5b7dc51ec329f3a4644026399a35c54d98"),
}
CATALOG_NAMES = ("AppIcon", "appicon", "screen-distance", "close_button_neutral", "ZZZZPackedAsset-1.0.1-gamut0", "Missing", "")


def encode(data):
    return base64.b64encode(data).decode("ascii")


def case(identity, args, files=None, env=None):
    item = {"id": identity, "args": args, "files": {name: encode(data) for name, data in (files or {}).items()}}
    if env:
        item["env"] = env
    return item


def name(size, scale):
    return f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


@lru_cache(maxsize=None)
def png(width, height, seed=0, color=6, depth=8, interlace=0, extra=b""):
    """Return a PNG image with a seeded pattern in any standard color type, bit depth, and interlace method."""
    channels = CHANNELS[color]
    base = bytes((x * (3 + seed % 5) + c * 61 + seed * 17) & 255 for x in range(width) for c in range(channels))
    rows = [base.translate(TABLES[(y * (5 + seed % 7)) & 255]) for y in range(height)]

    def pack(samples):
        if depth == 16:
            return bytes(v for b in samples for v in (b, b ^ 0x5A))
        if depth == 8:
            return samples
        values, per = [b >> (8 - depth) for b in samples], 8 // depth
        values += [0] * (-len(values) % per)
        return bytes(sum(v << (8 - depth * (i + 1)) for i, v in enumerate(values[n:n + per])) for n in range(0, len(values), per))

    raw = bytearray()
    for x0, y0, dx, dy in ADAM7 if interlace else ((0, 0, 1, 1),):
        for y in range(y0, height, dy) if x0 < width else ():
            row = rows[y] if dx == 1 else b"".join(rows[y][x * channels:(x + 1) * channels] for x in range(x0, width, dx))
            raw += b"\0" + pack(row)
    palette = chunk(b"PLTE", bytes((i * 37 + seed * 11 + c * 85) & 255 for i in range(1 << depth) for c in range(3))) if color == 3 else b""
    header = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, depth, color, 0, 0, interlace))
    return b"\x89PNG\r\n\x1a\n" + header + palette + extra + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")


def bmp(size, seed):
    rows = b"".join(bytes((x * 7 + y * 13 + seed + c * 50) & 255 for x in range(size) for c in range(4)) for y in range(size))
    info = struct.pack("<IiiHHIIiiII", 40, size, size, 1, 32, 0, len(rows), 2835, 2835, 0, 0)
    return b"BM" + struct.pack("<IHHI", 54 + len(rows), 0, 0, 54) + info + rows


def tiff(size, seed):
    pixels = bytes((x * 7 + y * 13 + seed + c * 50) & 255 for y in range(size) for x in range(size) for c in range(4))
    tags = ((256, 3, size), (257, 3, size), (258, 3, 8 + 2 + 10 * 12 + 4), (259, 3, 1), (262, 3, 2), (273, 4, 8 + 2 + 10 * 12 + 4 + 8), (277, 3, 4), (278, 3, size), (279, 4, len(pixels)), (338, 3, 2))
    body = b"".join(struct.pack(">HHI", tag, kind, 4 if tag == 258 else 1) + (struct.pack(">HH", value, 0) if kind == 3 and tag != 258 else struct.pack(">I", value)) for tag, kind, value in tags)
    return b"MM\0*" + struct.pack(">IH", 8, len(tags)) + body + bytes(4) + struct.pack(">HHHH", 8, 8, 8, 8) + pixels


def packbits(data):
    """Encode bytes with the icns run-length scheme: 0-127 copy n+1 bytes, 128-255 repeat one byte n-125 times."""
    out, i = bytearray(), 0
    while i < len(data):
        run = 1
        while i + run < len(data) and run < 130 and data[i + run] == data[i]:
            run += 1
        if run >= 3:
            out += bytes((run + 125, data[i]))
            i += run
            continue
        start = i
        while i < len(data) and i - start < 128 and not (i + 2 < len(data) and data[i] == data[i + 1] == data[i + 2]):
            i += 1
        out += bytes((i - start - 1,)) + data[start:i]
    return bytes(out)


def entry(kind, body):
    return kind + struct.pack(">I", len(body) + 8) + body


def icns(entries):
    body = b"".join(entries)
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def plane(count, seed, step=1):
    return bytes(((k * step) // 3 + seed * 29) & 255 for k in range(count))


def rgb(kind, size, seed, rle=True):
    planes = [plane(size * size, seed + c, c + 1) for c in range(3)]
    return entry(kind, (bytes(4) if kind == b"it32" else b"") + b"".join(packbits(p) if rle else p for p in planes))


def argb(kind, size, seed):
    return entry(kind, b"ARGB" + b"".join(packbits(plane(size * size, seed + c, c + 2)) for c in range(4)))


def mask(kind, size, seed):
    return entry(kind, plane(size * size, seed, 5))


def bits(kind, count, seed):
    return entry(kind, plane(count, seed, 7))


LEGACY = {
    "is32": lambda seed: [rgb(b"is32", 16, seed), mask(b"s8mk", 16, seed)],
    "il32": lambda seed: [rgb(b"il32", 32, seed), mask(b"l8mk", 32, seed)],
    "ih32": lambda seed: [rgb(b"ih32", 48, seed), mask(b"h8mk", 48, seed)],
    "it32": lambda seed: [rgb(b"it32", 128, seed), mask(b"t8mk", 128, seed)],
    "is32-nomask": lambda seed: [rgb(b"is32", 16, seed)],
    "is32-raw": lambda seed: [rgb(b"is32", 16, seed, rle=False), mask(b"s8mk", 16, seed)],
    "s8mk-only": lambda seed: [mask(b"s8mk", 16, seed)],
    "ICN#": lambda seed: [bits(b"ICN#", 256, seed)],
    "ics#": lambda seed: [bits(b"ics#", 64, seed)],
    "icm#": lambda seed: [bits(b"icm#", 48, seed)],
    "ich#": lambda seed: [bits(b"ich#", 576, seed)],
    "icl8": lambda seed: [bits(b"icl8", 1024, seed), bits(b"ICN#", 256, seed)],
    "icl4": lambda seed: [bits(b"icl4", 512, seed), bits(b"ICN#", 256, seed)],
    "ics8": lambda seed: [bits(b"ics8", 256, seed), bits(b"ics#", 64, seed)],
    "ics4": lambda seed: [bits(b"ics4", 128, seed)],
    "ich8": lambda seed: [bits(b"ich8", 2304, seed), bits(b"ich#", 576, seed)],
    "ic04-argb": lambda seed: [argb(b"ic04", 16, seed)],
    "ic05-argb": lambda seed: [argb(b"ic05", 32, seed)],
    "icsb-argb": lambda seed: [argb(b"icsb", 18, seed)],
}
PNG_TYPES = {"ic04": (16, 1), "ic05": (32, 1), "ic07": (128, 1), "ic08": (256, 1), "ic09": (512, 1), "ic10": (512, 2), "ic11": (16, 2), "ic12": (32, 2), "ic13": (128, 2), "ic14": (256, 2), "icp4": (16, 1), "icp5": (32, 1), "icp6": (64, 1), "icsb": (18, 1), "icsB": (18, 2), "sb24": (24, 1), "SB24": (24, 2)}


def modern(seed, kinds=("ic07", "ic08", "ic09", "ic10", "ic11", "ic12", "ic13", "ic14")):
    return [entry(kind.encode(), png(PNG_TYPES[kind][0] * PNG_TYPES[kind][1], PNG_TYPES[kind][0] * PNG_TYPES[kind][1], seed)) for kind in kinds] + [argb(b"ic04", 16, seed), argb(b"ic05", 32, seed)]


def iconset(folder, seed, slots=SLOTS, **options):
    return {f"{folder}/{name(size, scale)}": png(size * scale, size * scale, seed + size + scale, **options) for size, scale in slots}


def catalog(label):
    path, digest = CATALOGS[label]
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"The asset catalog differs from the pinned macOS build: {path}")
    return data


def core():
    full, icon = iconset("full.iconset", 1), {"full.icns": icns(modern(1))}
    result = [case(f"usage/{label}", args) for label, args in (("none", []), ("short-help", ["-h"]), ("long-help", ["--help"]), ("help-with-input", ["-h", "-c", "icns", "full.iconset"]))]
    result += [case(f"usage/{label}", args, full) for label, args in (("unknown-short", ["-x", "full.iconset"]), ("unknown-long", ["--bogus", "full.iconset"]), ("missing-convert-value", ["-c"]), ("missing-output-value", ["-c", "icns", "full.iconset", "-o"]), ("no-convert", ["full.iconset"]))]
    for label, args in (("bad-value", ["-c", "foo"]), ("uppercase", ["-c", "ICNS"]), ("licns", ["-c", "licns"]), ("empty", ["-c", ""]), ("long", ["--convert", "icns"]), ("long-equals", ["--convert=icns"]), ("attached", ["-cicns"]), ("abbreviated", ["--conv", "icns"]), ("repeated", ["-c", "iconset", "-c", "icns"]), ("repeated-bad", ["-c", "icns", "-c", "bad"])):
        result.append(case(f"convert-option/{label}", args + ["full.iconset"], full))
    for label, args, files in (
        ("short", ["-o", "x.icns"], {}), ("long", ["--output", "x.icns"], {}), ("long-equals", ["--output=x.icns"], {}), ("attached", ["-ox.icns"], {}),
        ("before-input", None, {}), ("wrong-extension", ["-o", "x.png"], {}), ("no-extension", ["-o", "x"], {}), ("dot-only", ["-o", ".icns"], {}),
        ("uppercase-extension", ["-o", "x.ICNS"], {}), ("iconset-extension", ["-o", "x.iconset"], {}), ("subdirectory", ["-o", "sub/x.icns"], {"sub/keep": b""}),
        ("missing-directory", ["-o", "nodir/x.icns"], {}), ("existing-file", ["-o", "x.icns"], {"x.icns": b"old"}), ("existing-directory", ["-o", "x.icns"], {"x.icns/keep": b""}),
        ("repeated", ["-o", "a.icns", "-o", "b.icns"], {}), ("space", ["-o", "my icon.icns"], {}), ("unicode", ["-o", "été.icns"], {}), ("double-extension", ["-o", "x.iconset.icns"], {}),
    ):
        result.append(case(f"output-option/{label}", ["-c", "icns", "-o", "x.icns", "full.iconset"] if args is None else ["-c", "icns", "full.iconset", *args], {**full, **files}))
    for label, args, files in (
        ("iconset-wrong-extension", ["-c", "iconset", "full.icns", "-o", "x.icns"], icon), ("iconset-short", ["-c", "iconset", "full.icns", "-o", "x.iconset"], icon),
        ("iconset-existing", ["-c", "iconset", "full.icns", "-o", "x.iconset"], {**icon, "x.iconset/old.png": b"old"}), ("iconset-existing-file", ["-c", "iconset", "full.icns", "-o", "x.iconset"], {**icon, "x.iconset": b"old"}),
        ("iconset-missing-directory", ["-c", "iconset", "full.icns", "-o", "nodir/x.iconset"], icon),
    ):
        result.append(case(f"output-option/{label}", args, files))
    for label, args, files in (
        ("iconset", ["-c", "icns", "full.iconset"], full), ("icns", ["-c", "iconset", "full.icns"], icon),
        ("no-extension", ["-c", "icns", "full"], iconset("full", 1)), ("other-extension", ["-c", "icns", "full.dir"], iconset("full.dir", 1)),
        ("icns-no-extension", ["-c", "iconset", "full"], {"full": icns(modern(1))}), ("icns-other-extension", ["-c", "iconset", "full.png"], {"full.png": icns(modern(1))}),
        ("subdirectory", ["-c", "icns", "sub/full.iconset"], iconset("sub/full.iconset", 1)), ("icns-subdirectory", ["-c", "iconset", "sub/full.icns"], {"sub/full.icns": icns(modern(1))}),
        ("trailing-slash", ["-c", "icns", "full.iconset/"], full), ("dot-prefix", ["-c", "icns", "./full.iconset"], full), ("dot-dot", ["-c", "icns", "sub/../full.iconset"], {**full, "sub/keep": b""}),
        ("existing-icns", ["-c", "icns", "full.iconset"], {**full, "full.icns": b"old"}), ("existing-iconset", ["-c", "iconset", "full.icns"], {**icon, "full.iconset/keep.txt": b"old"}),
        ("same-path", ["-c", "iconset", "full.iconset"], full), ("space", ["-c", "icns", "my icon.iconset"], iconset("my icon.iconset", 1)),
    ):
        result.append(case(f"default-output/{label}", args, files))
    for seed in (1, 2, 3):
        result.append(case(f"iconset-to-icns/full-{seed}", ["-c", "icns", "a.iconset"], iconset("a.iconset", seed)))
        result.append(case(f"icns-to-iconset/modern-{seed}", ["-c", "iconset", "a.icns"], {"a.icns": icns(modern(seed))}))
    result.append(case("iconset-to-icns/opaque", ["-c", "icns", "a.iconset"], iconset("a.iconset", 4, color=2)))
    result.append(case("icns-to-iconset/reversed", ["-c", "iconset", "a.icns"], {"a.icns": icns(modern(5)[::-1])}))
    for label, args, files in (
        ("missing-iconset", ["-c", "icns", "none.iconset"], {}), ("missing-icns", ["-c", "iconset", "none.icns"], {}),
        ("icns-as-iconset", ["-c", "icns", "full.icns"], icon), ("iconset-as-icns", ["-c", "iconset", "full.iconset"], full),
        ("file-as-iconset", ["-c", "icns", "f.iconset"], {"f.iconset": b"x\n"}), ("garbage-icns", ["-c", "iconset", "g.icns"], {"g.icns": b"garbage\n"}),
        ("empty-icns-file", ["-c", "iconset", "g.icns"], {"g.icns": b""}), ("empty-container", ["-c", "iconset", "g.icns"], {"g.icns": icns([])}),
        ("text-only-iconset", ["-c", "icns", "t.iconset"], {"t.iconset/readme.txt": b"hi\n"}), ("no-input", ["-c", "icns"], {}), ("no-input-iconset", ["-c", "iconset"], {}),
        ("percent-name", ["-c", "icns", "%s%n.iconset"], {}), ("extra-operands", ["-c", "icns", "full.iconset", "name", "more"], full),
    ):
        result.append(case(f"errors/{label}", args, files))
    return result


def sizes():
    result = []
    for size, scale in SLOTS:
        label = name(size, scale)[5:-4]
        result.append(case(f"icon-sizes/{label}", ["-c", "icns", "a.iconset"], iconset("a.iconset", 7, ((size, scale),))))
        result.append(case(f"icon-sizes/without-{label}", ["-c", "icns", "a.iconset"], iconset("a.iconset", 8, tuple(slot for slot in SLOTS if slot != (size, scale)))))
        pixels = size * scale
        for kind, width, height in (("half", pixels // 2, pixels // 2), ("double", pixels * 2, pixels * 2), ("plus-one", pixels + 1, pixels + 1), ("wide", pixels, pixels // 2)):
            if 0 < width <= 2048:
                result.append(case(f"image-validation/{label}-{kind}", ["-c", "icns", "a.iconset"], {f"a.iconset/{name(size, scale)}": png(width, height, 9)}))
    for label, files in (
        ("only-1x", iconset("a.iconset", 10, tuple(slot for slot in SLOTS if slot[1] == 1))), ("only-2x", iconset("a.iconset", 11, tuple(slot for slot in SLOTS if slot[1] == 2))),
        ("64", {"a.iconset/icon_64x64.png": png(64, 64, 1)}), ("64@2x", {"a.iconset/icon_64x64@2x.png": png(128, 128, 1)}), ("48", {"a.iconset/icon_48x48.png": png(48, 48, 1)}),
        ("24", {"a.iconset/icon_24x24.png": png(24, 24, 1)}), ("18", {"a.iconset/icon_18x18.png": png(18, 18, 1)}), ("1024", {"a.iconset/icon_1024x1024.png": png(1024, 1024, 1)}),
        ("@3x", {"a.iconset/icon_16x16@3x.png": png(48, 48, 1)}), ("@1x", {"a.iconset/icon_16x16@1x.png": png(16, 16, 1)}), ("uppercase", {"a.iconset/ICON_16X16.PNG": png(16, 16, 1)}),
        ("no-extension", {"a.iconset/icon_16x16": png(16, 16, 1)}), ("jpg-extension", {"a.iconset/icon_16x16.jpg": png(16, 16, 1)}), ("subfolder", {"a.iconset/sub/icon_16x16.png": png(16, 16, 1)}),
        ("duplicate-slot", {"a.iconset/icon_32x32.png": png(32, 32, 1), "a.iconset/icon_16x16@2x.png": png(32, 32, 2)}),
        ("content-decides", {"a.iconset/icon_16x16.png": png(32, 32, 1), "a.iconset/icon_32x32.png": png(32, 32, 2)}),
        ("full-with-extras", {**iconset("a.iconset", 12), "a.iconset/icon_64x64.png": png(64, 64, 1), "a.iconset/README.txt": b"hi\n", "a.iconset/.DS_Store": b"\0\0\0\1Bud1", "a.iconset/sub/x.png": png(16, 16, 1)}),
        ("full-with-one-bad", {**iconset("a.iconset", 13), "a.iconset/icon_16x16.png": png(17, 17, 1)}),
    ):
        result.append(case(f"icon-sizes/{label}", ["-c", "icns", "a.iconset"], files))
    return result


def images():
    result = []
    formats = [(color, depth, interlace) for color, depths in ((0, (1, 2, 4, 8, 16)), (2, (8, 16)), (3, (1, 2, 4, 8)), (4, (8, 16)), (6, (8, 16))) for depth in depths for interlace in (0, 1)]
    for color, depth, interlace in formats:
        for size, scale in ((16, 1), (128, 2)):
            label = f"color{color}-depth{depth}{'-interlaced' if interlace else ''}-{size}{'@2x' if scale == 2 else ''}"
            result.append(case(f"png-formats/{label}", ["-c", "icns", "a.iconset"], {f"a.iconset/{name(size, scale)}": png(size * scale, size * scale, 14, color, depth, interlace)}))
    chunks = {
        "gama": chunk(b"gAMA", struct.pack(">I", 100000)), "srgb": chunk(b"sRGB", b"\0"), "chrm": chunk(b"cHRM", struct.pack(">8I", 31270, 32900, 64000, 33000, 30000, 60000, 15000, 6000)),
        "phys": chunk(b"pHYs", struct.pack(">IIB", 5669, 5669, 1)), "text": chunk(b"tEXt", b"Comment\0rustify"), "bad-iccp": chunk(b"iCCP", b"icc\0\0" + zlib.compress(b"not a profile")),
        "unknown-ancillary": chunk(b"ruSt", b"data"), "unknown-critical": chunk(b"RUST", b"data"),
    }
    for label, extra in chunks.items():
        for size in (16, 128):
            result.append(case(f"png-formats/{label}-{size}", ["-c", "icns", "a.iconset"], {f"a.iconset/{name(size, 1)}": png(size, size, 15, extra=extra)}))
    result.append(case("png-formats/palette-trns", ["-c", "icns", "a.iconset"], {"a.iconset/icon_16x16.png": png(16, 16, 16, 3, 4, extra=chunk(b"tRNS", bytes(range(0, 256, 32))))}))
    for size in (16, 128):
        good = png(size, size, 17)
        header = lambda width, height, depth: b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, depth, 6, 0, 0, 0)) + good[33:]
        for label, data in (
            ("bad-crc", good[:-16] + bytes([good[-16] ^ 1]) + good[-15:]), ("truncated", good[:len(good) // 2]), ("header-only", good[:33]), ("no-iend", good[:-12]),
            ("bad-signature", b"\x89PNX" + good[4:]), ("idat-garbage", good[:33] + chunk(b"IDAT", b"x" * 10) + chunk(b"IEND", b"")), ("empty", b""), ("text", b"hello\n"),
            ("bmp", bmp(size, 1)), ("tiff", tiff(size, 1)), ("jpeg-magic", b"\xff\xd8\xff\xe0\0\x10JFIF\0" + bytes(32)), ("gif-magic", b"GIF89a\x10\0\x10\0" + bytes(16)),
            ("zero-width", header(0, size, 8)), ("huge-declared", header(1 << 20, 1 << 20, 8)), ("bad-depth", header(size, size, 3)),
        ):
            result.append(case(f"image-validation/{label}-{size}", ["-c", "icns", "a.iconset"], {f"a.iconset/{name(size, 1)}": data}))
            if size == 16:
                result.append(case(f"image-validation/{label}-in-full", ["-c", "icns", "a.iconset"], {**iconset("a.iconset", 18), "a.iconset/icon_16x16.png": data}))
    return result


def legacy():
    result = [case(f"legacy-entries/{label}", ["-c", "iconset", "a.icns"], {"a.icns": icns(build(19))}) for label, build in LEGACY.items()]
    result.append(case("legacy-entries/all-legacy", ["-c", "iconset", "a.icns"], {"a.icns": icns([item for label in ("is32", "il32", "ih32", "it32", "ICN#", "icl8") for item in LEGACY[label](20)])}))
    result.append(case("legacy-entries/legacy-and-modern", ["-c", "iconset", "a.icns"], {"a.icns": icns(LEGACY["is32"](21) + LEGACY["it32"](21) + modern(21))}))
    for kind, (size, scale) in PNG_TYPES.items():
        result.append(case(f"icns-to-iconset/png-{kind}", ["-c", "iconset", "a.icns"], {"a.icns": icns([entry(kind.encode(), png(size * scale, size * scale, 22))])}))
        result.append(case(f"image-validation/png-{kind}-wrong-size", ["-c", "iconset", "a.icns"], {"a.icns": icns([entry(kind.encode(), png(40, 40, 23))])}))
    ic07 = entry(b"ic07", png(128, 128, 24))
    for label, entries in (
        ("toc", [entry(b"TOC ", b"ic07" + struct.pack(">I", len(ic07))), ic07]), ("icnv", [entry(b"icnV", struct.pack(">f", 1.0)), ic07]), ("name", [entry(b"name", b"icon"), ic07]),
        ("info", [entry(b"info", b"bplist00garbage"), ic07]), ("dark", [ic07, entry(b"\xfd\xd9/\xa8", icns([entry(b"ic07", png(128, 128, 25))]))]), ("unknown", [entry(b"zzzz", b"abc"), ic07]),
        ("duplicate", [ic07, entry(b"ic07", png(128, 128, 26))]), ("jpeg2000", [entry(b"ic08", b"\0\0\0\x0cjP  \r\n\x87\n" + bytes(32))]), ("argb-png", [entry(b"ic04", png(16, 16, 27))]),
        ("png-garbage", [entry(b"ic07", b"\x89PNG\r\n\x1a\n" + bytes(40))]), ("empty-entry", [entry(b"ic07", b""), entry(b"ic08", png(256, 256, 28))]),
    ):
        result.append(case(f"legacy-entries/{label}", ["-c", "iconset", "a.icns"], {"a.icns": icns(entries)}))
    good = icns(modern(29, ("ic07", "ic11")))
    for label, data in (
        ("header-too-long", good[:4] + struct.pack(">I", len(good) + 100) + good[8:]), ("header-too-short", good[:4] + struct.pack(">I", 8) + good[8:]),
        ("truncated", good[:len(good) // 2]), ("entry-zero-length", good[:12] + struct.pack(">I", 0) + good[16:]), ("entry-overflow", good[:12] + struct.pack(">I", 1 << 30) + good[16:]),
        ("bad-magic", b"ICNS" + good[4:]), ("header-only", good[:8]), ("trailing-bytes", good + b"junk"),
    ):
        result.append(case(f"errors/icns-{label}", ["-c", "iconset", "a.icns"], {"a.icns": data}))
    return result


def environment():
    full, result = iconset("a.iconset", 30), []
    for variable, label in (("ICONCOMPILER_SEPARATE_HIDPI", "separate-hidpi"), ("ICONCOMPILER_GENERATE_BASE_SYSTEM_ICNS", "base-system-icns")):
        for value in ("1", "YES", "yes", "0", "", "true", "2", "01", " 1"):
            result.append(case(f"{label}/value-{value.strip() or 'empty'}{'-space' if value.startswith(' ') else ''}", ["-c", "icns", "a.iconset"], full, {variable: value}))
        for slots, kind in ((tuple(slot for slot in SLOTS if slot[1] == 1), "only-1x"), (tuple(slot for slot in SLOTS if slot[1] == 2), "only-2x"), (((16, 1), (16, 2)), "small")):
            result.append(case(f"{label}/{kind}", ["-c", "icns", "a.iconset"], iconset("a.iconset", 31, slots), {variable: "1"}))
        result.append(case(f"{label}/output", ["-c", "icns", "a.iconset", "-o", "out/b.icns"], {**full, "out/keep": b""}, {variable: "1"}))
        result.append(case(f"{label}/to-iconset", ["-c", "iconset", "a.icns"], {"a.icns": icns(modern(32))}, {variable: "1"}))
        result.append(case(f"{label}/catalog", ["-c", "icns", "Assets.car", "AppIcon"], {"Assets.car": catalog("iconset")}, {variable: "1"}))
    result.append(case("separate-hidpi/with-base", ["-c", "icns", "a.iconset"], full, {"ICONCOMPILER_SEPARATE_HIDPI": "1", "ICONCOMPILER_GENERATE_BASE_SYSTEM_ICNS": "1"}))
    result.append(case("separate-hidpi/existing-2x", ["-c", "icns", "a.iconset"], {**full, "a@2x.icns": b"old"}, {"ICONCOMPILER_SEPARATE_HIDPI": "1"}))
    return result


def catalogs():
    result = []
    for label in CATALOGS:
        data = catalog(label)
        for icon in CATALOG_NAMES[:-1]:
            for target in ("icns", "iconset"):
                result.append(case(f"asset-catalog/{label}-{icon}-{target}", ["-c", target, "Assets.car", icon], {"Assets.car": data}))
    data = catalog("iconset")
    for label, args, files in (
        ("output", ["-c", "icns", "-o", "x.icns", "Assets.car", "AppIcon"], {}), ("output-iconset", ["-c", "iconset", "-o", "x.iconset", "Assets.car", "AppIcon"], {}),
        ("output-wrong-extension", ["-c", "icns", "-o", "x.iconset", "Assets.car", "AppIcon"], {}), ("subdirectory", ["-c", "icns", "sub/Assets.car", "AppIcon"], None),
        ("renamed", ["-c", "icns", "icons.bin", "AppIcon"], None), ("existing", ["-c", "icns", "Assets.car", "AppIcon"], {"AppIcon.icns": b"old"}),
        ("extra-operand", ["-c", "icns", "Assets.car", "AppIcon", "more"], {}), ("empty-name", ["-c", "icns", "Assets.car", ""], {}),
    ):
        files = {"sub/Assets.car": data} if label == "subdirectory" else {"icons.bin": data} if label == "renamed" else {"Assets.car": data, **files}
        result.append(case(f"asset-catalog/{label}", args, files))
    for label, args, files in (
        ("no-name", ["-c", "icns", "Assets.car"], {"Assets.car": data}), ("missing-catalog", ["-c", "icns", "none.car", "AppIcon"], {}),
        ("garbage-catalog", ["-c", "icns", "g.car", "AppIcon"], {"g.car": b"hello\n"}), ("directory-catalog", ["-c", "icns", "d.car", "AppIcon"], {"d.car/keep": b""}),
        ("iconset-with-name", ["-c", "icns", "a.iconset", "AppIcon"], iconset("a.iconset", 33)), ("icns-with-name", ["-c", "iconset", "a.icns", "AppIcon"], {"a.icns": icns(modern(33))}),
        ("truncated-catalog", ["-c", "icns", "Assets.car", "AppIcon"], {"Assets.car": data[:len(data) // 2]}),
    ):
        result.append(case(f"icon-name/{label}", args, files))
    return result


def manual():
    """Return one case for each claim of the manual page and the usage text."""
    full, icon = iconset("a.iconset", 34), {"a.icns": icns(modern(34))}
    rows = (
        ("usage/synopsis-usage-text", ["-h"], {}), ("convert-option/synopsis-short-icns", ["-c", "icns", "a.iconset"], full), ("convert-option/synopsis-short-iconset", ["-c", "iconset", "a.icns"], icon),
        ("convert-option/manual-long-convert", ["--convert", "iconset", "a.icns"], icon), ("output-option/manual-long-output", ["--convert", "icns", "--output", "b.icns", "a.iconset"], full),
        ("output-option/synopsis-output-icns", ["-c", "icns", "-o", "b.icns", "a.iconset"], full), ("output-option/synopsis-output-iconset", ["-c", "iconset", "-o", "b.iconset", "a.icns"], icon),
        ("default-output/manual-same-directory-icns", ["-c", "icns", "d/a.iconset"], iconset("d/a.iconset", 34)), ("default-output/manual-same-directory-iconset", ["-c", "iconset", "d/a.icns"], {"d/a.icns": icns(modern(34))}),
        ("default-output/manual-icon-name-icns", ["-c", "icns", "d/Assets.car", "AppIcon"], {"d/Assets.car": catalog("iconset")}),
        ("default-output/manual-icon-name-iconset", ["-c", "iconset", "d/Assets.car", "AppIcon"], {"d/Assets.car": catalog("iconset")}),
        ("asset-catalog/manual-extract-icns", ["-c", "icns", "Assets.car", "AppIcon"], {"Assets.car": catalog("layered")}),
        ("asset-catalog/manual-extract-iconset", ["-c", "iconset", "Assets.car", "AppIcon"], {"Assets.car": catalog("layered")}),
        ("errors/usage-convert-required", ["a.iconset"], full), ("errors/usage-file-required", ["-c", "icns"], {}),
    )
    return [case(identity, args, files) for identity, args, files in rows]


def generate(count=300, seed=20261025):
    """Return seeded probes over every option, option form, input kind, and environment flag."""
    rng = random.Random(seed)
    options = {"short": lambda v: ["-o", v], "long": lambda v: ["--output", v], "equals": lambda v: [f"--output={v}"], "attached": lambda v: [f"-o{v}"]}
    converts = {"short": lambda v: ["-c", v], "long": lambda v: ["--convert", v], "equals": lambda v: [f"--convert={v}"], "attached": lambda v: [f"-c{v}"]}
    result = []
    for number in range(count):
        kind = rng.choice(("iconset", "iconset", "iconset", "icns", "icns", "catalog", "argv"))
        files, operands = {}, []
        if kind == "iconset":
            folder = rng.choice(("a.iconset", "dir/b.iconset", "c", "my icon.iconset"))
            for size, scale in SLOTS:
                if rng.random() < 0.5:
                    pixels = size * scale if rng.random() < 0.85 else rng.choice((size * scale * 2, size * scale // 2 or 1, size * scale + 1))
                    if pixels > 1024 and rng.random() < 0.7:
                        pixels = size * scale
                    color = rng.choice((6, 6, 6, 2, 0, 3, 4))
                    depth = rng.choice({0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 8, 16)}[color]) if pixels <= 256 else 8
                    data = png(pixels, pixels, rng.randrange(4) if pixels > 256 else rng.randrange(1000), color, depth, int(pixels <= 128 and rng.random() < 0.2))
                    if rng.random() < 0.08:
                        data = rng.choice((data[:rng.randrange(1, len(data))], bmp(size, 1), b"", data[:-12]))
                    files[f"{folder}/{name(size, scale)}"] = data
            if rng.random() < 0.2:
                files[f"{folder}/{rng.choice(('notes.txt', 'icon_64x64.png', 'icon_16x16@3x.png', '.DS_Store'))}"] = png(64, 64, 3) if rng.random() < 0.5 else b"x"
            files = files or {f"{folder}/readme.txt": b"x"}
            operands, target = [folder + rng.choice(("", "", "/"))], rng.choice(("icns", "icns", "icns", "iconset"))
        elif kind == "icns":
            source = rng.choice(("a.icns", "dir/b.icns", "c", "d.png"))
            # PNG data in ic05 and icp6 gives undefined pixels on the reference (see README), so the fixed cases cover them.
            pool = list(LEGACY) + [kind for kind in PNG_TYPES if kind not in ("ic05", "icp6")] + ["modern", "info", "toc", "unknown"]
            entries = []
            for label in rng.sample(pool, rng.randrange(1, 6)):
                if label in LEGACY:
                    entries += LEGACY[label](rng.randrange(1000))
                elif label in PNG_TYPES:
                    size, scale = PNG_TYPES[label]
                    entries.append(entry(label.encode(), png(size * scale, size * scale, rng.randrange(4) if size * scale > 256 else rng.randrange(1000))))
                elif label == "modern":
                    entries += modern(rng.randrange(4))
                else:
                    entries.append(entry({"info": b"info", "toc": b"TOC ", "unknown": b"abcd"}[label], plane(rng.randrange(0, 40), number)))
            rng.shuffle(entries)
            data = icns(entries)
            if rng.random() < 0.1:
                data = data[:rng.randrange(8, len(data))]
            files, operands, target = {source: data}, [source], rng.choice(("iconset", "iconset", "iconset", "icns"))
        elif kind == "catalog":
            label = rng.choice(("iconset", "iconset", "layered", "glyph", "noicon"))
            source = rng.choice(("Assets.car", "dir/Assets.car", "icons"))
            files, operands, target = {source: catalog(label)}, [source, rng.choice(CATALOG_NAMES[:-1] + ("AppIcon",) * 3)], rng.choice(("icns", "iconset"))
        else:
            files, target = iconset("a.iconset", 35, ((16, 1), (16, 2))), rng.choice(("icns", "iconset", "ICNS", "x", ""))
            operands = rng.sample(["a.iconset", "a.icns", "name", "-h", "--help", "-x", "--", "-o"], rng.randrange(0, 4))
        args = converts[rng.choice(tuple(converts))](target) if rng.random() < 0.95 else []
        if rng.random() < 0.4:
            output = rng.choice(("out", "dir/out", "x y", "nodir/out")) + "." + rng.choice((target, target, target, "png", "icns", "iconset", "ICNS", ""))
            if output.startswith("dir/"):
                files.setdefault("dir/keep", b"")
            args += options[rng.choice(tuple(options))](output)
        position = rng.randrange(len(args) + 1)
        args = args[:position] + operands + args[position:]
        env = {}
        for variable in ("ICONCOMPILER_SEPARATE_HIDPI", "ICONCOMPILER_GENERATE_BASE_SYSTEM_ICNS"):
            if rng.random() < 0.12:
                env[variable] = rng.choice(("1", "YES", "0", "yes"))
        feature = {"iconset": "iconset-to-icns", "icns": "icns-to-iconset", "catalog": "asset-catalog", "argv": "convert-option"}[kind]
        result.append(case(f"{feature}/generated-{number:03d}", args, files, env))
    return result


def chains():
    """Return multi-step scenarios whose later steps read the outputs of earlier steps."""
    trip = [["-c", "icns", "a.iconset", "-o", "x1.icns"], ["-c", "iconset", "x1.icns", "-o", "s1.iconset"], ["-c", "icns", "s1.iconset", "-o", "x2.icns"], ["-c", "iconset", "x2.icns", "-o", "s2.iconset"]]
    result = [{"id": f"iconset-to-icns/roundtrip-{seed}", "files": iconset("a.iconset", seed, **options), "steps": trip} for seed, options in ((40, {}), (41, {"color": 2}), (42, {"color": 3, "depth": 4}), (43, {"color": 0, "depth": 16}))]
    result.append({"id": "iconset-to-icns/roundtrip-partial", "files": iconset("a.iconset", 44, ((16, 1), (128, 2), (512, 1))), "steps": trip})
    reverse = [["-c", "iconset", "a.icns", "-o", "s0.iconset"], ["-c", "icns", "s0.iconset", "-o", "x1.icns"], ["-c", "iconset", "x1.icns", "-o", "s1.iconset"], ["-c", "icns", "s1.iconset", "-o", "x2.icns"]]
    result += [{"id": f"legacy-entries/roundtrip-{label}", "files": {"a.icns": icns(LEGACY[label](45))}, "steps": reverse} for label in ("is32", "il32", "it32", "ICN#", "icl8")]
    result.append({"id": "icns-to-iconset/roundtrip-modern", "files": {"a.icns": icns(modern(46))}, "steps": reverse})
    result.append({"id": "asset-catalog/roundtrip", "files": {"Assets.car": catalog("iconset")}, "steps": [["-c", "iconset", "Assets.car", "AppIcon", "-o", "s0.iconset"], ["-c", "icns", "s0.iconset", "-o", "x1.icns"], ["-c", "iconset", "x1.icns", "-o", "s1.iconset"], ["-c", "icns", "s1.iconset", "-o", "x2.icns"]]})
    result.append({"id": "separate-hidpi/roundtrip", "files": iconset("a.iconset", 47), "env": {"ICONCOMPILER_SEPARATE_HIDPI": "1"}, "steps": [["-c", "icns", "a.iconset", "-o", "x1.icns"], ["-c", "iconset", "x1@2x.icns", "-o", "s1.iconset"], ["-c", "icns", "s1.iconset", "-o", "x2.icns"]]})
    return result
