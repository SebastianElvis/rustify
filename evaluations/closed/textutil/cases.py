"""Define the textutil cases for each distinguisher class and milestone."""

import base64
import random

import documents as make

FORMATS = ["txt", "html", "rtf", "rtfd", "doc", "docx", "wordml", "odt", "webarchive"]
SUFFIX = {"wordml": "xml"}
META = [("title", "Title &<x>"), ("author", "Ann \u00c9"), ("subject", "Subj"), ("keywords", "(k1, k2, \"k 3\")"), ("comment", "Line one"), ("editor", "Ed"), ("company", "Co"), ("creationtime", "2020-01-02T03:04:05Z"), ("modificationtime", "2021-02-03T04:05:06Z")]
TEXTS = {
    "simple": b"Hello world\nSecond line\n",
    "empty": b"",
    "no-newline": b"no trailing newline",
    "crlf": b"one\r\ntwo\r\n\r\nfour\r\n",
    "cr": b"one\rtwo\r",
    "unicode": "caf\u00e9 \u263a \u65e5\u672c\u8a9e \U0001F600 \u05e9\u05dc\u05d5\u05dd\n".encode(),
    "controls": b"tab\there\x0cform\x0bvt\x00nul\n",
    "rtf-special": b"{braces} \\back\\slash \\par\n",
    "html-special": b"<b>&amp; \"q\" 'a'</b>\n",
    "blank-lines": b"\n\n\nmiddle\n\n\n",
    "long": (" ".join(make.words(9, 400)) + "\n").encode(),
    "latin1": b"caf\xe9 na\xefve\n",
    "invalid-utf8": b"bad \xff\xfe\xc3 end\n",
    "utf8-bom": b"\xef\xbb\xbfbom text\n",
    "utf16le-bom": b"\xff\xfe" + "utf16 \u263a\n".encode("utf-16-le"),
    "utf16be-bom": b"\xfe\xff" + "utf16 \u263a\n".encode("utf-16-be"),
    "spaces": b"  leading\ttabs\t\ttrailing   \n",
    "generated": "\n".join(make.paragraphs(3, 5, 9)).encode(),
}


def encode(data):
    return base64.b64encode(data).decode("ascii")


def name(fmt, stem="doc"):
    return f"{stem}.{SUFFIX.get(fmt, fmt)}"


def document(fmt, seed=1):
    """Return the fixture files for one generated document."""
    if fmt == "txt":
        return {name(fmt): TEXTS["generated"] if seed == 1 else "\n".join(make.paragraphs(seed)).encode()}
    if fmt == "rtfd":
        return {f"doc.rtfd/{key}": value for key, value in make.rtfd(seed).items()}
    if fmt == "html":
        return {name(fmt): make.html(seed, "pic.png"), "pic.png": make.png()}
    data = {"rtf": lambda: make.rtf(seed, info=True, table=True), "doc": lambda: make.doc(seed), "docx": lambda: make.docx(seed), "wordml": lambda: make.wordml(seed), "odt": lambda: make.odt(seed), "webarchive": lambda: make.webarchive(seed)}[fmt]()
    return {name(fmt): data}


def case(identity, args, files=None, stdin=b"", steps=None):
    row = {"id": identity, "steps": steps or [args], "files": {key: encode(value) for key, value in (files or {}).items()}}
    if stdin:
        row["stdin_b64"] = encode(stdin)
    return row


def surface():
    txt = {"foo.txt": TEXTS["simple"]}
    rtf = {"foo.rtf": make.rtf(1), "a.rtf": make.rtf(2), "b.rtf": make.rtf(3, table=True)}
    rows = [
        case("help/no-arguments", []),
        case("help/help", ["-help"]),
        case("help/help-extra", ["-help", "foo.txt"], txt),
        case("help/unknown-option", ["-bogus"]),
        case("help/file-only", ["foo.txt"], txt),
        case("info/manual-example", ["-info", "foo.rtf"], rtf),
        case("convert/manual-example", ["-convert", "html", "foo.rtf"], rtf),
        case("font/manual-example", ["-convert", "rtf", "-font", "Times", "-fontsize", "10", "foo.txt"], txt),
        case("cat/manual-example", ["-cat", "html", "-title", "Several Files", "-output", "index.html", "a.rtf", "b.rtf", "foo.rtf"], rtf),
        case("errors/convert-no-format", ["-convert"]),
        case("errors/cat-no-format", ["-cat"]),
        case("errors/invalid-format", ["-convert", "xyz", "foo.txt"], txt),
        case("errors/convert-no-input", ["-convert", "rtf"]),
        case("errors/cat-no-input", ["-cat", "rtf"]),
        case("errors/info-no-input", ["-info"]),
        case("errors/missing-file", ["-convert", "rtf", "missing.txt"]),
        case("errors/missing-and-present", ["-convert", "rtf", "missing.txt", "foo.txt"], txt),
        case("errors/info-missing", ["-info", "missing.txt", "foo.txt"], txt),
        case("errors/info-folder", ["-info", "folder"], {"folder/inner.txt": b"x\n"}),
        case("errors/convert-folder", ["-convert", "rtf", "folder"], {"folder/inner.txt": b"x\n"}),
        case("errors/output-missing-value", ["-convert", "rtf", "-output"]),
        case("errors/output-missing-folder", ["-convert", "rtf", "-output", "sub/out.rtf", "foo.txt"], txt),
        case("errors/empty-extension", ["-convert", "rtf", "-extension", "", "foo.txt"], txt),
        case("errors/extension-missing-value", ["-convert", "rtf", "-extension"]),
        case("errors/multiple-commands", ["-convert", "txt", "-cat", "txt", "foo.txt"], txt),
        case("errors/info-and-convert", ["-info", "-convert", "txt", "foo.txt"], txt),
        case("errors/stdin-and-files", ["-cat", "txt", "-stdin", "-stdout", "foo.txt"], txt, b"x\n"),
        case("errors/invalid-encoding", ["-convert", "txt", "-encoding", "bogus", "-stdout", "foo.txt"], txt),
        case("errors/invalid-inputencoding", ["-convert", "txt", "-inputencoding", "bogus", "-stdout", "foo.txt"], txt),
        case("errors/invalid-input-format", ["-convert", "html", "-format", "bogus", "foo.txt"], txt),
        case("errors/wrong-input-format", ["-convert", "html", "-format", "doc", "-stdout", "foo.rtf"], rtf),
        case("errors/invalid-fontsize", ["-convert", "rtf", "-fontsize", "abc", "foo.txt"], txt),
        case("errors/zero-fontsize", ["-convert", "rtf", "-fontsize", "0", "foo.txt"], txt),
        case("errors/negative-fontsize", ["-convert", "rtf", "-fontsize", "-5", "foo.txt"], txt),
        case("errors/invalid-prefixspaces", ["-convert", "html", "-prefixspaces", "abc", "-stdout", "foo.txt"], txt),
        case("errors/invalid-multiplier", ["-convert", "html", "-textsizemultiplier", "x", "-stdout", "foo.txt"], txt),
        case("errors/invalid-timeout", ["-convert", "html", "-timeout", "x", "-stdout", "foo.txt"], txt),
        case("errors/invalid-creationtime", ["-convert", "rtf", "-creationtime", "yesterday", "-stdout", "foo.txt"], txt),
        case("errors/unconvertible-output", ["-convert", "txt", "-encoding", "iso-8859-1", "-stdout", "foo.txt"], {"foo.txt": TEXTS["unicode"]}),
        case("errors/inapplicable-input-encoding", ["-convert", "txt", "-inputencoding", "utf-8", "-stdout", "foo.txt"], {"foo.txt": TEXTS["latin1"]}),
        case("errors/corrupt-docx", ["-convert", "txt", "-stdout", "bad.docx"], {"bad.docx": b"PK\x03\x04broken"}),
        case("errors/corrupt-doc", ["-convert", "txt", "-stdout", "bad.doc"], {"bad.doc": bytes.fromhex("D0CF11E0A1B11AE1") + b"\0" * 504}),
        case("errors/corrupt-webarchive", ["-info", "bad.webarchive"], {"bad.webarchive": b"bplist00garbage"}),
        case("end-of-options/dash-file", ["-convert", "html", "--", "-x.txt"], {"-x.txt": b"dash\n"}),
        case("end-of-options/dash-without-marker", ["-convert", "html", "-x.txt"], {"-x.txt": b"dash\n"}),
        case("end-of-options/option-after-marker", ["-info", "--", "-stdout"], {"-stdout": b"named\n"}),
        case("exit-status/partial-failure", ["-cat", "txt", "-output", "out.txt", "foo.txt", "missing.txt"], txt),
    ]
    samples = {"output": "o.html", "extension": "x", "encoding": "utf-8", "inputencoding": "utf-8", "format": "txt", "font": "Courier", "fontsize": "10", "baseurl": "file:///b/", "timeout": "20", "textsizemultiplier": "2", "excludedelements": "(span)", "prefixspaces": "2", **dict(META)}
    for option, value in samples.items():
        rows.append(case(f"{option}/multiple", ["-convert", "html", f"-{option}", value, f"-{option}", value, "-stdout", "foo.txt"], txt))
        rows.append(case(f"{option}/missing-value", ["-convert", "html", "foo.txt", f"-{option}"], txt))
    for flag in ("noload", "nostore", "strip", "stdin", "stdout", "noversion"):
        rows.append(case(f"{flag}/repeated", ["-convert", "html", f"-{flag}", f"-{flag}", "-stdout", "foo.txt"], txt))
    for fmt in ("html", "rtf", "docx", "odt", "doc", "wordml", "webarchive"):
        rows.append(case(f"noversion/{fmt}", ["-convert", fmt, "-noversion", "-output", "out." + SUFFIX.get(fmt, fmt), "foo.txt"], txt))
    rows += [
        case("output/with-stdout", ["-convert", "rtf", "-output", "a.rtf", "-stdout", "foo.txt"], txt),
        case("baseurl/empty", ["-convert", "html", "-baseurl", "", "-stdout", "foo.txt"], txt),
        case("baseurl/relative", ["-convert", "html", "-baseurl", "relative/path", "-stdout", "foo.txt"], txt),
        case("excludedelements/unclosed", ["-convert", "html", "-excludedelements", "(a", "-stdout", "foo.txt"], txt),
        case("keywords/unparsable", ["-convert", "html", "-keywords", "a, b", "-stdout", "foo.txt"], txt),
        case("info/singular-size", ["-info", "one.txt"], {"one.txt": b"x"}),
        case("info/copyright", ["-info", "c.rtf"], {"c.rtf": b"{\\rtf1{\\info{\\*\\copyright Me 2020}{\\*\\company Acme}}x\\par}"}),
        case("info/unknown-type", ["-info", "data.bin"], {"data.bin": bytes(range(256))}),
    ]
    for option, value in META:
        rows.append(case(f"{option}/documented", ["-convert", "html", f"-{option}", value, "-stdout", "foo.txt"], txt))
    for option in ("noload", "nostore", "strip"):
        rows.append(case(f"{option}/documented", ["-convert", "html", f"-{option}", "-stdout", "foo.rtf"], rtf))
    for option, value in (("baseurl", "file:///base/"), ("timeout", "20"), ("textsizemultiplier", "1.5"), ("excludedelements", "(span)"), ("prefixspaces", "4")):
        rows.append(case(f"{option}/documented", ["-convert", "html", f"-{option}", value, "-stdout", "foo.rtf"], rtf))
    return rows


def core():
    rows = []
    for key, data in TEXTS.items():
        files = {"in.txt": data}
        rows += [case(f"txt/to-rtf-{key}", ["-convert", "rtf", "in.txt"], files), case(f"txt/to-txt-{key}", ["-convert", "txt", "-output", "out.txt", "in.txt"], files), case(f"info/txt-{key}", ["-info", "in.txt"], files)]
    for label, data in (("plain", make.rtf(1)), ("info", make.rtf(2, info=True)), ("table", make.rtf(3, table=True)), ("image", make.rtf(4, image=True)), ("all", make.rtf(5, True, True, True)), ("minimal", b"{\\rtf1 hi}"), ("unbalanced", b"{\\rtf1\\ansi open {\\b bold"), ("unicode-skip", b"{\\rtf1\\ansi\\uc2\\u8364  xx euro\\u-3913 ?? end\\par}"), ("ansicpg", b"{\\rtf1\\ansi\\ansicpg1251\\'c0\\'e1\\par}"), ("mac", b"{\\rtf1\\mac\\'8e\\'a5\\par}"), ("hidden", b"{\\rtf1 shown {\\v hidden} {\\*\\unknown skip} done\\par}")):
        files = {"in.rtf": data}
        rows += [case(f"rtf/to-txt-{label}", ["-convert", "txt", "in.rtf"], files), case(f"rtf/to-rtf-{label}", ["-convert", "rtf", "-output", "out.rtf", "in.rtf"], files), case(f"info/rtf-{label}", ["-info", "in.rtf"], files)]
    two = {"a.txt": b"first\n", "b.txt": TEXTS["unicode"], "c.rtf": make.rtf(6)}
    rows += [
        case("cat/txt-two-files", ["-cat", "txt", "a.txt", "b.txt"], two),
        case("cat/rtf-mixed", ["-cat", "rtf", "a.txt", "c.rtf", "b.txt"], two),
        case("cat/default-name", ["-cat", "rtf", "a.txt", "b.txt"], two),
        case("cat/output", ["-cat", "txt", "-output", "joined.text", "c.rtf", "a.txt"], two),
        case("cat/stdout", ["-cat", "rtf", "-stdout", "a.txt", "b.txt"], two),
        case("cat/same-file-twice", ["-cat", "txt", "-stdout", "a.txt", "a.txt"], two),
        case("cat/no-trailing-newline", ["-cat", "txt", "-stdout", "x.txt", "y.txt"], {"x.txt": b"x", "y.txt": b"y"}),
        case("info/multiple", ["-info", "a.txt", "b.txt", "c.rtf"], two),
        case("stdin/convert", ["-convert", "rtf", "-stdin"], stdin=TEXTS["simple"]),
        case("stdin/convert-stdout", ["-convert", "rtf", "-stdin", "-stdout"], stdin=TEXTS["unicode"]),
        case("stdin/rtf-document", ["-convert", "txt", "-stdin", "-stdout"], stdin=make.rtf(7)),
        case("stdin/info", ["-info", "-stdin"], stdin=TEXTS["simple"]),
        case("stdin/info-rtf", ["-info", "-stdin"], stdin=make.rtf(8, info=True)),
        case("stdin/cat", ["-cat", "txt", "-stdin"], stdin=b"cat\n"),
        case("stdin/output", ["-convert", "txt", "-stdin", "-output", "named.txt"], stdin=b"named\n"),
        case("stdin/empty", ["-convert", "rtf", "-stdin", "-stdout"]),
        case("stdout/convert", ["-convert", "rtf", "-stdout", "a.txt"], two),
        case("stdout/first-only", ["-convert", "txt", "-stdout", "a.txt", "c.rtf"], two),
        case("stdout/with-output", ["-convert", "txt", "-stdout", "-output", "o.txt", "a.txt"], two),
        case("output/convert", ["-convert", "rtf", "-output", "renamed.rtf", "a.txt"], two),
        case("output/first-only", ["-convert", "rtf", "-output", "renamed.rtf", "a.txt", "b.txt"], two),
        case("output/other-extension", ["-convert", "rtf", "-output", "renamed.data", "a.txt"], two),
        case("output/subfolder", ["-convert", "txt", "-output", "sub/o.txt", "c.rtf"], {**two, "sub/keep": b""}),
        case("output/overwrite-input", ["-convert", "txt", "-output", "a.txt", "c.rtf"], two),
        case("output/in-place", ["-convert", "txt", "a.txt"], two),
        case("extension/convert", ["-convert", "rtf", "-extension", "foo", "a.txt", "b.txt"], two),
        case("extension/dotted", ["-convert", "txt", "-extension", ".x", "c.rtf"], two),
        case("extension/with-output", ["-convert", "rtf", "-extension", "foo", "-output", "o.rtf", "a.txt", "b.txt"], two),
        case("extension/subfolder-input", ["-convert", "rtf", "-extension", "r", "sub/in.txt"], {"sub/in.txt": b"sub\n"}),
        case("end-of-options/after-files", ["-convert", "rtf", "a.txt", "--", "b.txt"], two),
        case("convert/option-order", ["-stdout", "-font", "Courier", "-convert", "rtf", "a.txt"], two),
        case("convert/repeated-option", ["-convert", "rtf", "-fontsize", "9", "-fontsize", "15", "-stdout", "a.txt"], two),
    ]
    for value in ["utf-8", "UTF-8", "utf-16", "utf-16be", "utf-16le", "utf-32", "iso-8859-1", "latin1", "windows-1252", "macintosh", "x-mac-roman", "us-ascii", "shift_jis", "euc-jp", "gb2312", "big5", "koi8-r", "iso-2022-jp", "1", "4", "5", "10", "12", "30", "2415919360", "0", "-1", "999"]:
        for key in ("latin1-text", "unicode"):
            files = {"in.txt": "caf\u00e9 na\u00efve\n".encode() if key == "latin1-text" else TEXTS["unicode"]}
            rows.append(case(f"encoding/txt-{value}-{key}", ["-convert", "txt", "-encoding", value, "-stdout", "in.txt"], files))
        rows.append(case(f"encoding/html-{value}", ["-convert", "html", "-encoding", value, "-stdout", "in.txt"], {"in.txt": TEXTS["unicode"]}))
    rows += [case("encoding/rtf-ignored", ["-convert", "rtf", "-encoding", "utf-16", "-stdout", "in.txt"], {"in.txt": TEXTS["unicode"]}), case("encoding/file-output", ["-convert", "txt", "-encoding", "utf-16le", "in.rtf"], {"in.rtf": make.rtf(9)})]
    for value in ["utf-8", "latin1", "iso-8859-1", "macintosh", "windows-1252", "utf-16le", "utf-16be", "utf-16", "shift_jis", "koi8-r", "5", "30", "10", "bogus"]:
        for key in ("latin1", "utf16le-bom", "unicode"):
            rows.append(case(f"inputencoding/{value}-{key}", ["-convert", "txt", "-inputencoding", value, "-stdout", "in.txt"], {"in.txt": TEXTS[key]}))
    rows.append(case("inputencoding/ignored-for-rtf", ["-convert", "txt", "-inputencoding", "utf-16", "-stdout", "in.rtf"], {"in.rtf": make.rtf(10)}))
    for fmt, source in (("txt", "in.rtf"), ("rtf", "in.txt"), ("html", "in.txt"), ("txt", "in.html"), ("rtf", "in.html"), ("doc", "in.txt"), ("docx", "in.txt"), ("odt", "in.rtf"), ("wordml", "in.txt"), ("webarchive", "in.txt"), ("rtfd", "in.rtf")):
        files = {"in.rtf": make.rtf(11), "in.txt": b"{\\rtf1 not rtf}\n<p>not html</p>\n", "in.html": make.html(12)}
        rows += [case(f"format/{fmt}-from-{source}", ["-convert", "txt", "-format", fmt, "-stdout", source], files), case(f"format/info-{fmt}-from-{source}", ["-info", "-format", fmt, source], files)]
    for font in ["Times", "Times-Roman", "Times-Bold", "Helvetica", "Helvetica-Bold", "Courier", "Menlo-Regular", "Menlo", "Monaco", "Georgia", "Arial", "NoSuchFont", ""]:
        rows.append(case(f"font/rtf-{font or 'empty'}", ["-convert", "rtf", "-font", font, "-stdout", "in.txt"], {"in.txt": TEXTS["simple"]}))
        rows.append(case(f"font/html-{font or 'empty'}", ["-convert", "html", "-font", font, "-stdout", "in.txt"], {"in.txt": TEXTS["simple"]}))
    rows.append(case("font/ignored-for-rtf-input", ["-convert", "rtf", "-font", "Courier", "-stdout", "in.rtf"], {"in.rtf": make.rtf(13)}))
    for size in ["1", "8", "10", "12.5", "13.25", "24", "72", "999", "1e2", " 9", "9pt"]:
        rows.append(case(f"fontsize/rtf-{size.strip()}{'-space' if size.startswith(' ') else ''}", ["-convert", "rtf", "-fontsize", size, "-stdout", "in.txt"], {"in.txt": TEXTS["simple"]}))
    rows.append(case("fontsize/html-with-font", ["-convert", "html", "-font", "Courier", "-fontsize", "9", "-stdout", "in.txt"], {"in.txt": TEXTS["simple"]}))
    return rows


def html_cases():
    rows = []
    variants = {
        "full": make.html(1, "pic.png"),
        "no-title": make.html(2, title=False),
        "no-style": make.html(3, style=False),
        "fragment": b"plain <b>bold</b> text",
        "latin1-meta": b"<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=iso-8859-1\"></head><body>caf\xe9</body></html>",
        "malformed": b"<html><body><p>open <b>bold <i>both</p><table><tr><td>cell</body>",
        "script": b"<html><head><script>document.write('x')</script><style>p{color:red}</style></head><body><p>after</p><noscript>ns</noscript></body></html>",
        "entities": b"<p>&lt;&gt;&amp;&quot;&apos;&copy;&reg;&trade;&hellip;&#169;&#x1F600;&unknown;</p>",
        "whitespace": b"<p>  many    spaces\n\nand\tlines  </p><pre>\tkeep\n  this</pre>",
        "lists": b"<ol start=\"3\"><li>three</li><li>four</li></ol><ul type=\"square\"><li>sq</li></ul><dl><dt>term</dt><dd>def</dd></dl>",
        "headings": b"<h1>1</h1><h2>2</h2><h3>3</h3><h4>4</h4><h5>5</h5><h6>6</h6>",
        "table-spans": b"<table border=\"2\" cellpadding=\"4\"><tr><td colspan=\"2\">wide</td></tr><tr><td rowspan=\"2\">tall</td><td>x</td></tr><tr><td>y</td></tr></table>",
        "fonts": b"<p><font face=\"Courier\" size=\"5\" color=\"#00ff00\">font</font> <span style=\"font-family: Georgia; font-weight: bold; font-style: italic; text-decoration: line-through\">span</span></p>",
        "empty": b"",
        "rtl": "<p dir=\"rtl\">\u05e9\u05dc\u05d5\u05dd \u0645\u0631\u062d\u0628\u0627</p>".encode(),
    }
    for label, data in variants.items():
        files = {"in.html": data, "pic.png": make.png()}
        for fmt in ("txt", "rtf", "html"):
            rows.append(case(f"html/{label}-to-{fmt}", ["-convert", fmt, "-output", f"out.{fmt}", "in.html"], files))
        rows.append(case(f"info/html-{label}", ["-info", "in.html"], files))
    for fmt in ("txt", "rtf"):
        rows.append(case(f"html/default-name-from-{fmt}", ["-convert", "html", "in." + fmt], {"in." + fmt: document(fmt, 4)[name(fmt)]}))
    image = {"in.html": make.html(5, "pic.png"), "pic.png": make.png(), "in.rtfd/TXT.rtf": make.rtfd(6)["TXT.rtf"], "in.rtfd/pic.png": make.png()}
    rich = {"in.rtf": make.rtf(7, True, True, True)}
    options = [
        ("noload", ["-noload"]), ("nostore", ["-nostore"]), ("baseurl", ["-baseurl", "file:///nowhere/"]), ("baseurl-http-noload", ["-noload", "-baseurl", "http://127.0.0.1:9/"]),
        ("timeout", ["-timeout", "20"]), ("timeout-zero", ["-timeout", "0"]),
        ("textsizemultiplier", ["-textsizemultiplier", "2"]), ("textsizemultiplier-half", ["-textsizemultiplier", "0.5"]), ("textsizemultiplier-zero", ["-textsizemultiplier", "0"]),
        ("excludedelements", ["-excludedelements", "(span, p)"]), ("excludedelements-empty", ["-excludedelements", "()"]), ("excludedelements-many", ["-excludedelements", "(XML, DOCTYPE, head, style, span, font, b, i, u, table)"]), ("excludedelements-bare", ["-excludedelements", "span"]),
        ("prefixspaces", ["-prefixspaces", "0"]), ("prefixspaces-large", ["-prefixspaces", "8"]), ("prefixspaces-negative", ["-prefixspaces", "-1"]),
    ]
    for label, extra in options:
        feature = label.split("-")[0]
        rows.append(case(f"{feature}/html-input-{label}", ["-convert", "html", *extra, "-output", "out.html", "in.html"], image))
        rows.append(case(f"{feature}/rtf-input-{label}", ["-convert", "html", *extra, "-stdout", "in.rtf"], rich))
        rows.append(case(f"{feature}/rtfd-input-{label}", ["-convert", "html", *extra, "-output", "out.html", "in.rtfd"], image))
        rows.append(case(f"{feature}/to-rtfd-{label}", ["-convert", "rtfd", *extra, "-output", "out.rtfd", "in.html"], image))
    rows += [
        case("html/stdin", ["-convert", "rtf", "-stdin", "-stdout"], stdin=make.html(8)),
        case("html/stdin-info", ["-info", "-stdin"], stdin=make.html(9)),
        case("html/attachment-to-stdout", ["-convert", "html", "-stdout", "in.rtfd"], image),
        case("html/cat", ["-cat", "html", "-output", "all.html", "in.html", "in.rtf"], image | rich),
        case("html/missing-image", ["-convert", "rtfd", "-output", "out.rtfd", "page.html"], {"page.html": b"<p>x <img src=\"none.png\"> y</p>"}),
        case("html/encoding-utf-16", ["-convert", "html", "-encoding", "utf-16", "-stdout", "in.rtf"], rich),
    ]
    return rows


def archive_cases():
    rows = []
    for source in FORMATS:
        files = document(source, 20 + FORMATS.index(source))
        path = name(source)
        rows.append(case(f"{source}/info", ["-info", path], files))
        for target in FORMATS:
            rows.append(case(f"{target}/from-{source}", ["-convert", target, "-output", "out." + SUFFIX.get(target, target), path], files))
    for target in FORMATS:
        if target != "rtfd":
            rows.append(case(f"stdout/{target}", ["-convert", target, "-stdout", "in.rtf"], {"in.rtf": make.rtf(30, True, True)}))
        rows.append(case(f"{target}/default-name", ["-convert", target, "in.txt"], {"in.txt": TEXTS["simple"]}))
        rows.append(case(f"cat/{target}", ["-cat", target, "-output", "joined." + SUFFIX.get(target, target), "a.rtf", "b.txt"], {"a.rtf": make.rtf(31), "b.txt": TEXTS["unicode"]}))
        rows.append(case(f"stdin/{target}-input", ["-convert", "rtf", "-stdin", "-stdout"], stdin=next(iter(document(target, 32).values())) if target != "rtfd" else make.rtf(32)))
    rows += [
        case("rtfd/image-rtf-to-rtfd", ["-convert", "rtfd", "-output", "out.rtfd", "in.rtf"], {"in.rtf": make.rtf(33, image=True)}),
        case("rtfd/to-rtf-drops-attachment", ["-convert", "rtf", "-output", "out.rtf", "doc.rtfd"], document("rtfd", 34)),
        case("webarchive/to-rtfd", ["-convert", "rtfd", "-output", "out.rtfd", "doc.webarchive"], document("webarchive", 35)),
        case("webarchive/no-subresources", ["-convert", "html", "-stdout", "w.webarchive"], {"w.webarchive": make.webarchive(36, image=False)}),
        case("docx/no-core-properties", ["-info", "x.docx"], {"x.docx": make.docx(37, meta=False)}),
        case("doc/stdin", ["-info", "-stdin"], stdin=make.doc(38)),
        case("odt/format-forced", ["-convert", "txt", "-format", "odt", "-stdout", "x.bin"], {"x.bin": make.odt(39)}),
        case("docx/format-forced", ["-convert", "txt", "-format", "docx", "-stdout", "x.bin"], {"x.bin": make.docx(40)}),
        case("wordml/extension-xml", ["-convert", "wordml", "-extension", "wordml", "in.txt"], {"in.txt": TEXTS["simple"]}),
    ]
    return rows


def metadata():
    rows = []
    sources = {"in.txt": TEXTS["simple"], "meta.rtf": make.rtf(41, info=True), "meta.docx": make.docx(42), "meta.odt": make.odt(43), "meta.xml": make.wordml(44), "meta.html": make.html(45), "meta.webarchive": make.webarchive(46, image=False)}
    for target in FORMATS:
        out = "out." + SUFFIX.get(target, target)
        for option, value in META:
            rows.append(case(f"{option}/{target}", ["-convert", target, f"-{option}", value, "-output", out, "in.txt"], sources))
        everything = [item for option, value in META for item in (f"-{option}", value)]
        rows.append(case(f"title/{target}-all-options", ["-convert", target, *everything, "-output", out, "in.txt"], sources))
        rows.append(case(f"info/{target}-all-options", ["-convert", target, *everything, "-output", out, "in.txt"], sources, steps=[["-convert", target, *everything, "-output", out, "in.txt"], ["-info", out]]))
        for source in ("meta.rtf", "meta.docx", "meta.odt", "meta.xml", "meta.html", "meta.webarchive"):
            rows.append(case(f"strip/{source.replace('.', '-')}-to-{target}", ["-convert", target, "-strip", "-output", out, source], sources))
            rows.append(case(f"convert/{source.replace('.', '-')}-keeps-metadata-to-{target}", ["-convert", target, "-output", out, source], sources))
        rows.append(case(f"strip/override-{target}", ["-convert", target, "-strip", "-title", "New", "-output", out, "meta.rtf"], sources))
    for value in ["2000-02-29T23:59:59Z", "1970-01-01T00:00:00Z", "1900-01-01T00:00:00Z", "2100-12-31T12:00:00Z", "2020-01-02T03:04:05+0100", "2020-01-02 03:04:05", "2020-13-40T99:99:99Z", ""]:
        for option in ("creationtime", "modificationtime"):
            rows.append(case(f"{option}/value-{value or 'empty'}", ["-convert", "rtf", f"-{option}", value, "-stdout", "in.txt"], sources))
    for value in ["(a)", "(a, b, c)", "a, b", "()", "(\"quoted, comma\", plain)", "(unclosed", ""]:
        rows.append(case(f"keywords/value-{value or 'empty'}", ["-convert", "html", "-keywords", value, "-stdout", "in.txt"], sources))
    rows += [
        case("title/empty", ["-convert", "html", "-title", "", "-stdout", "in.txt"], sources),
        case("title/unicode", ["-convert", "rtf", "-title", "\u65e5\u672c \U0001F600 {\\}", "-stdout", "in.txt"], sources),
        case("comment/multiline", ["-convert", "docx", "-comment", "a\nb", "-output", "o.docx", "in.txt"], sources),
        case("title/cat", ["-cat", "rtf", "-title", "Cat", "-stdout", "meta.rtf", "in.txt"], sources),
        case("strip/cat", ["-cat", "rtf", "-strip", "-stdout", "meta.rtf", "meta.docx"], sources),
    ]
    return rows


def roundtrip():
    rows = []
    for fmt in FORMATS:
        for key in ("simple", "unicode", "crlf", "generated"):
            middle = "mid." + SUFFIX.get(fmt, fmt)
            rows.append(case(f"{fmt}/roundtrip-txt-{key}", [], {"in.txt": TEXTS[key]}, steps=[["-convert", fmt, "-output", middle, "in.txt"], ["-convert", "txt", "-output", "back.txt", middle]]))
        for other in FORMATS:
            if other not in ("txt", fmt):
                first, second = "a." + SUFFIX.get(fmt, fmt), "b." + SUFFIX.get(other, other)
                rows.append(case(f"{fmt}/chain-rtf-{other}", [], {"in.rtf": make.rtf(50, True, True)}, steps=[["-convert", fmt, "-output", first, "in.rtf"], ["-convert", other, "-output", second, first], ["-convert", "rtf", "-output", "back.rtf", second]]))
    return rows


def generate(seed=20261025, count=240):
    """Draw seeded probes over commands, input formats, options, and option combinations."""
    rng = random.Random(seed)
    rows = []
    values = {"-encoding": ["utf-8", "utf-16", "iso-8859-1", "macintosh", "30", "10", "bogus"], "-inputencoding": ["utf-8", "latin1", "utf-16le", "shift_jis", "5"], "-format": FORMATS + ["bogus"],
              "-font": ["Times", "Courier", "Helvetica-Bold", "Zapfino", "NoSuchFont"], "-fontsize": ["8", "11.5", "36", "0", "x"], "-baseurl": ["file:///g/"], "-timeout": ["0", "20", "60"],
              "-textsizemultiplier": ["0.75", "1.25", "3"], "-excludedelements": ["(span)", "(p, b)", "(font, i, table)"], "-prefixspaces": ["0", "1", "3"], "-extension": ["out", "gen"],
              **{f"-{option}": [value, value[::-1] if "time" not in option else "2001-01-01T00:00:00Z"] for option, value in META}}
    flags = ["-noload", "-nostore", "-strip", "-stdout"]
    for index in range(count):
        source = rng.choice(FORMATS)
        files = document(source, 100 + index)
        if source == "txt":
            files = {"doc.txt": rng.choice(list(TEXTS.values())) + make.words(index, rng.randrange(1, 30)).encode()}
        command = rng.choice(["-convert", "-convert", "-convert", "-cat", "-info"])
        args = [command] + ([] if command == "-info" else [rng.choice(FORMATS)])
        for option in rng.sample(sorted(values), rng.randrange(0, 5)):
            args += [option, rng.choice(values[option])]
        args += rng.sample(flags, rng.randrange(0, 3))
        inputs = [name(source)]
        stdin = b""
        if rng.random() < 0.15 and source != "rtfd":
            stdin, inputs = files.pop(name(source)), []
            args.append("-stdin")
        elif rng.random() < 0.3:
            extra = rng.choice(["txt", "rtf", "html"])
            files[name(extra, "two")] = next(iter(document(extra, 200 + index).values()))
            inputs.append(name(extra, "two"))
        if rng.random() < 0.2 and command != "-info":
            args += ["-output", "gen-out." + rng.choice(["txt", "rtf", "html", "bin"])]
        if rng.random() < 0.1:
            args.append("--")
        feature = args[args.index("-format") + 1] if "-format" in args and args[args.index("-format") + 1] in FORMATS else source
        rows.append(case(f"{feature}/generated-{index:03d}", args + inputs, files, stdin))
    return rows


def reports():
    groups = {
        "surface-manual": surface(),
        "replay-core": core(),
        "replay-html": html_cases(),
        "replay-archive": archive_cases(),
        "replay-metadata": metadata(),
        "metamorphic-roundtrip": roundtrip(),
        "generate-options": generate(),
    }
    identities = [row["id"] for rows in groups.values() for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("The case ids must be unique.")
    return groups
