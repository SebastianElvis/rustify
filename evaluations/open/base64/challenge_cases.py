"""Generate separate deterministic evaluation cases."""

import base64
import random


def cases():
    result = []

    def add(identity, args, data=b"", files=None):
        item = {"id": identity, "args": args, "stdin_b64": base64.b64encode(data).decode("ascii")}
        if files is not None:
            item["files"] = {name: base64.b64encode(value).decode("ascii") for name, value in files.items()}
        result.append(item)

    rng = random.Random(20261024)
    for size in (0, 1, 2, 3, 4, 55, 56, 57, 58, 59, 255, 256, 4095, 4096, 4097, 30719, 30720, 30721):
        data = bytes(rng.randrange(256) for _ in range(size))
        add(f"encode-{size}", [], data)
        add(f"unwrap-{size}", ["-w0"], data)
        encoded = base64.b64encode(data)
        add(f"decode-{size}", ["--decode"], encoded)
        add(f"unpadded-{size}", ["-d"], encoded.rstrip(b"="))
    for width in (0, 1, 2, 3, 4, 5, 7, 75, 76, 77, 2147483648):
        add(f"width-{width}", ["--wrap=" + str(width)], bytes(range(256)))
    for number, data in enumerate((b"=", b"==", b"===", b"====", b"A", b"AB", b"ABC", b"ABCD", b"Zh==", b"Zm9=", b"Zg=", b"Zg===", b"Zg==Zg==", b"Zg=\n=", b"Zg\r\n==", b"Zg\t==", b"Zm9v\x00", b"Zm9v\xff", b"Zg==a", b"Zg!Zg")):
        add(f"malformed-{number}", ["-d"], data)
        add(f"garbage-{number}", ["-di"], data)
    alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r\t!?\x00\xff"
    for number in range(120):
        data = bytes(rng.choice(alphabet) for _ in range(rng.randrange(1, 90)))
        add(f"generated-{number}", ["-di"] if number % 2 else ["-d"], data)
    for number, args in enumerate((
        ["--help"], ["--version"], ["--de"], ["--ign", "-d"], ["--wr=3"],
        ["-idw0"], ["-w"], ["--wrap"], ["--wrap="], ["--decode=1"], ["--unknown"],
        ["-x"], ["-dx"], ["-w", "-1"], ["-w", "+1"], ["-w", " 2"], ["-w", "1k"],
        ["-w", "9999999999999999999999999999999999999"], ["a", "b"], ["missing"],
        ["file", "-w0"], ["--", "-d"], ["-", "--wrap=0"],
    )):
        add(f"options-{number}", args, b"hello", {"file": b"world", "-d": b"test"})
    for number, filename in enumerate(("plain", "space name", "quote'name", "nested/file", "caf\u00e9")):
        add(f"file-{number}", [filename, "-w0"], files={filename: bytes(range(256))})
        add(f"file-decode-{number}", ["-d", filename], files={filename: b"aGVsbG8="})
    add("directory-input", ["folder"], files={"folder/file": b"data"})
    add("newline-input", ["-d"], b"\n\n\n")
    add("all-garbage", ["-di"], bytes(range(256)))
    return result

