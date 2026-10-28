"""Check textutil outputs with parsers that are independent of both programs."""

import base64
from html.parser import HTMLParser
import io
import plistlib
import re
import struct
import xml.etree.ElementTree as ElementTree
import zipfile

VOID = {"meta", "br", "img", "hr", "link", "input", "col", "base", "area", "param"}
RTF_TOKEN = re.compile(rb"\\([a-zA-Z]{1,32})(-?\d{1,10})? ?|\\'([0-9a-fA-F]{2})|\\[^a-zA-Z']|[{}]|[^\\{}]+", re.S)


def rtf(data):
    """Tokenize RTF by the RTF 1.9.1 grammar: a balanced group tree with valid control words."""
    if not data.startswith(b"{\\rtf1"):
        raise ValueError("RTF must start with {\\rtf1.")
    depth, position, closed = 0, 0, False
    while position < len(data):
        match = RTF_TOKEN.match(data, position)
        if not match or closed and data[position:].strip(b"\0\r\n "):
            raise ValueError(f"Invalid RTF at byte {position}.")
        token = match.group(0)
        position = match.end()
        if match.group(1) == b"bin":
            position += int(match.group(2) or 0)
        elif match.group(1) == b"u" and not -32768 <= int(match.group(2) or 0) <= 65535:
            raise ValueError("A \\u value is out of range.")
        depth += {b"{": 1, b"}": -1}.get(token, 0)
        if depth < 0:
            raise ValueError("RTF closes a group that is not open.")
        if depth == 0 and token == b"}":
            closed = True
            if data[position:].strip(b"\0\r\n "):
                raise ValueError("RTF has data after the document group.")
            break
    if not closed:
        raise ValueError("RTF does not close the document group.")
    return {"pictures": data.count(b"\\NeXTGraphic ")}


class Nesting(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.charset = [], None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "meta" and "charset=" in (values.get("content") or ""):
            self.charset = values["content"].split("charset=")[1]
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack.pop() != tag:
            raise ValueError(f"The HTML end tag {tag} does not match the open element.")


def html(data):
    """Check that HTML elements nest and that the bytes decode with the declared charset."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\0" in data[:2]:
        charset = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-16-be" if data[:1] == b"\0" else "utf-16-le"
        text = data.decode(charset)
    else:
        probe = Nesting()
        probe.feed(data.decode("latin-1"))
        charset = probe.charset or "utf-8"
        text = data.decode(charset)
    parser = Nesting()
    parser.feed(text)
    parser.close()
    if parser.stack:
        raise ValueError(f"The HTML elements {parser.stack} stay open.")
    return {"charset": charset}


def package(data):
    """Check a docx or odt package with zipfile and an XML parser for each XML part."""
    bundle = zipfile.ZipFile(io.BytesIO(data))
    if bundle.testzip() is not None:
        raise ValueError("A zip entry has a bad CRC.")
    names = bundle.namelist()
    for item in names:
        if item.endswith((".xml", ".rels")):
            ElementTree.fromstring(bundle.read(item))
    if names[0] == "mimetype":
        first = bundle.infolist()[0]
        if first.compress_type != zipfile.ZIP_STORED or bundle.read("mimetype") != b"application/vnd.oasis.opendocument.text" or "content.xml" not in names:
            raise ValueError("The ODF package does not follow the ODF packaging rules.")
        return {"kind": "odt"}
    if "[Content_Types].xml" not in names or "word/document.xml" not in names:
        raise ValueError("The OOXML package lacks its main parts.")
    return {"kind": "docx"}


def wordml(data):
    root = ElementTree.fromstring(data)
    if root.tag != "{http://schemas.microsoft.com/office/word/2003/wordml}wordDocument":
        raise ValueError("The root is not a WordprocessingML 2003 document.")
    return {"kind": "wordml"}


def webarchive(data):
    value = plistlib.loads(data)
    main = value["WebMainResource"]
    if not isinstance(main["WebResourceData"], bytes) or main["WebResourceMIMEType"] != "text/html":
        raise ValueError("The web archive main resource is not HTML.")
    html(main["WebResourceData"])
    for resource in value.get("WebSubresources", []):
        if not isinstance(resource["WebResourceData"], bytes) or not resource["WebResourceURL"]:
            raise ValueError("A web archive subresource is incomplete.")
    return {"subresources": len(value.get("WebSubresources", []))}


def doc(data):
    """Read the MS-CFB directory, find the WordDocument stream, and check the FIB identifier."""
    if data[:8] != bytes.fromhex("D0CF11E0A1B11AE1"):
        raise ValueError("The compound file signature is missing.")
    shift = struct.unpack_from("<H", data, 30)[0]
    size = 1 << shift
    sector = lambda number: data[(number + 1) * size:(number + 2) * size]
    fat = [entry for number in struct.unpack_from("<109I", data, 76) if number < 0xFFFFFFFA for entry in struct.unpack(f"<{size // 4}I", sector(number))]

    def chain(start):
        out, seen = b"", set()
        while start < 0xFFFFFFFA and start not in seen:
            seen.add(start)
            out, start = out + sector(start), fat[start]
        return out

    directory = chain(struct.unpack_from("<I", data, 48)[0])
    for offset in range(0, len(directory), 128):
        length = struct.unpack_from("<H", directory, offset + 64)[0]
        if directory[offset:offset + length - 2].decode("utf-16-le", "replace") == "WordDocument":
            stream = chain(struct.unpack_from("<I", directory, offset + 116)[0])
            if struct.unpack_from("<H", stream, 0)[0] != 0xA5EC:
                raise ValueError("The FIB identifier is wrong.")
            return {"kind": "doc"}
    raise ValueError("The WordDocument stream is missing.")


PARSERS = {"rtf": rtf, "html": html, "docx": package, "odt": package, "wordml": wordml, "webarchive": webarchive, "doc": doc}
EXTENSIONS = {"wordml": "xml"}


def attachments(missing):
    def rtfd(data):
        if missing:
            raise ValueError(f"The RTFD attachments are missing: {missing}")
        return rtf(data)
    return rtfd


def kind(data):
    for prefix, parser in ((b"{\\rtf", rtf), (b"PK\x03\x04", package), (b"bplist00", webarchive), (bytes.fromhex("D0CF11E0"), doc)):
        if data.startswith(prefix):
            return parser
    head = data[:400].lstrip(b"\xef\xbb\xbf").lower()
    if head.startswith(b"<?xml") and b"worddocument" in head:
        return wordml
    if head.startswith((b"<!doctype html", b"<html")):
        return html
    return None


def outputs(case, result):
    """Yield each document output of one run: changed files, RTFD packages, and standard output."""
    targets = [args[args.index(command) + 1] for args in case["steps"] for command in ("-convert", "-cat") if command in args[:-1]]
    expected = {PARSERS[target] for target in targets if target in PARSERS}
    for path, item in result["files"].items():
        data = base64.b64decode(item["data_b64"])
        if case["files"].get(path) == item["data_b64"]:
            continue
        if path.endswith(".rtfd/TXT.rtf") and "rtfd" in targets:
            folder = path[:-len("TXT.rtf")]
            names = re.findall(rb"\\NeXTGraphic (.+?) \\", data)
            yield path, data, attachments([name.decode() for name in names if folder + name.decode() not in result["files"]])
        elif kind(data) in expected:
            yield path, data, kind(data)
        elif any(path.endswith("." + EXTENSIONS.get(target, target)) for target in targets if target in PARSERS):
            yield path, data, PARSERS[next(target for target in targets if path.endswith("." + EXTENSIONS.get(target, target)))]
    for index, (args, step) in enumerate(zip(case["steps"], result["steps"])):
        data = base64.b64decode(step["stdout_b64"])
        target = next((args[args.index(command) + 1] for command in ("-convert", "-cat") if command in args[:-1]), None)
        if data and step["returncode"] == 0 and target in PARSERS and "-stdout" in args:
            yield f"stdout{index + 1}", data, PARSERS[target]


def check(cases, runs):
    """Parse every candidate output, and report a parser that rejects a reference output as an oracle defect."""
    rows, failures = [], []
    for case in cases:
        reference, candidate = runs[case["id"]][0][0], runs[case["id"]][1]
        for path, data, parser in outputs(case, reference):
            try:
                parser(data)
            except Exception as error:
                failures.append(f"The independent parser rejects the reference output {case['id']}:{path}: {error}")
        for path, data, parser in outputs(case, candidate):
            try:
                parser(data)
                error = None
            except Exception as problem:
                error = f"{type(problem).__name__}: {problem}"
            rows.append({"input": {"id": f"{case['id']}/{path}"}, "parser": parser.__name__, "error": error, "differences": [] if error is None else ["parse"], "passed": error is None})
    return {"status": "passed" if rows and all(row["passed"] for row in rows) else "failed", "passed": sum(row["passed"] for row in rows), "failed": sum(not row["passed"] for row in rows), "cases": rows}, failures
