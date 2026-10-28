"""Generate textutil input documents deterministically from public format specifications."""

import io
import plistlib
import random
import struct
import zipfile
import zlib

WORDS = ["alpha", "beta", "gamma", "delta", "caf\u00e9", "na\u00efve", "\u00fcber", "\u03bb", "\u65e5\u672c", "\u263a", "tab\there", "x&y", "<tag>", "\"quote\"", "\u2014", "\U0001F600"]


def words(seed, count):
    rng = random.Random(seed)
    return " ".join(rng.choice(WORDS) for _ in range(count))


def paragraphs(seed, count=3, size=6):
    return [words(seed * 100 + index, size) for index in range(count)]


def png(width=4, height=2, rgb=(255, 0, 0)):
    """Write a truecolor PNG (RFC 2083)."""
    chunk = lambda kind, data: struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    rows = b"".join(b"\0" + bytes(rgb) * width for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def rtf_text(text):
    out = []
    for char in text:
        code = ord(char)
        if char in "\\{}":
            out.append("\\" + char)
        elif char == "\t":
            out.append("\\tab ")
        elif code < 128:
            out.append(char)
        elif code < 256:
            out.append(f"\\'{code:02x}")
        else:
            for unit in struct.unpack(f"<{len(char.encode('utf-16-le')) // 2}h", char.encode("utf-16-le")):
                out.append(f"\\uc1\\u{unit}?")
    return "".join(out)


def rtf(seed, info=False, table=False, image=False):
    """Write RTF 1.9.1 with fonts, colors, styles, alignment, a field, and optional parts."""
    lines = paragraphs(seed)
    body = [
        "\\pard\\qc\\f1\\fs32\\b " + rtf_text(lines[0]) + "\\b0\\par",
        "\\pard\\ql\\fi360\\li720\\sa120\\f0\\fs24\\i " + rtf_text(lines[1]) + "\\i0  \\ul under\\ulnone  \\strike s\\strike0  \\cf2 red\\cf0  super{\\super 2} \\line next\\par",
        "\\pard\\qr\\tx1440\\tx2880 " + rtf_text(lines[2]) + "\\tab end {\\field{\\*\\fldinst{HYPERLINK \"http://example.com/" + str(seed) + "\"}}{\\fldrslt link}}\\par",
    ]
    if table:
        body.append("\\trowd\\trgaph108\\cellx2000\\cellx4000\\pard\\intbl a1\\cell b1\\cell\\row\\trowd\\trgaph108\\cellx2000\\cellx4000\\pard\\intbl a2\\cell b2\\cell\\row\\pard")
    if image:
        body.append("{\\pict\\pngblip\\picw4\\pich2\\picwgoal80\\pichgoal40 " + png().hex() + "}\\par")
    meta = "{\\info{\\title Title " + str(seed) + "}{\\author Author}{\\keywords k1, k2}{\\creatim\\yr2011\\mo2\\dy3\\hr4\\min5\\sec6}}" if info else ""
    header = "{\\rtf1\\ansi\\ansicpg1252\\deff0{\\fonttbl{\\f0\\froman Times New Roman;}{\\f1\\fswiss Helvetica;}{\\f2\\fmodern Courier;}}{\\colortbl;\\red0\\green0\\blue0;\\red255\\green0\\blue0;}"
    return (header + meta + "\n" + "\n".join(body) + "\n}").encode("ascii")


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")


def html(seed, image=None, title=True, style=True):
    """Write HTML 4.01 with headings, inline styles, lists, a table, and entities."""
    lines = paragraphs(seed, 4)
    head = (f"<title>Page {seed}</title><meta name=\"author\" content=\"Writer {seed}\">" if title else "") + ("<style>p.big {font-size: 18px; color: #336699} .c {text-align: center}</style>" if style else "")
    parts = [
        f"<h1>{escape(lines[0])}</h1>",
        f"<p class=\"big\">{escape(lines[1])} <b>bold</b> <i>italic</i> <u>under</u> <s>strike</s> <sub>sub</sub> <sup>sup</sup> <code>code</code> <a href=\"http://example.com/{seed}\">link</a></p>",
        f"<p class=\"c\">{escape(lines[2])}<br>after break &eacute; &#x263A; &nbsp;&nbsp;spaces</p>",
        "<ul><li>one</li><li>two<ol><li>nested</li></ol></li></ul>",
        "<table border=\"1\"><tr><th>h1</th><th>h2</th></tr><tr><td>a</td><td>b</td></tr></table>",
        f"<pre>{escape(lines[3])}\n  indented</pre><blockquote>quoted</blockquote><hr><h2>Sub</h2><div style=\"font-family: Courier; font-size: 10px\">div text</div>",
    ]
    if image:
        parts.append(f"<p>pic <img src=\"{image}\" width=\"4\" height=\"2\"> end</p>")
    return f"<!DOCTYPE html><html><head><meta charset=\"utf-8\">{head}</head><body>{''.join(parts)}</body></html>".encode()


def rtfd(seed):
    """Write an RTFD package: TXT.rtf with a NeXTGraphic attachment and the image file."""
    text = rtf(seed).decode("ascii")[:-2] + "\n\\pard pic {{\\NeXTGraphic pic.png \\width80 \\height40}\xac} end\\par\n}"
    return {"TXT.rtf": text.encode("latin-1"), "pic.png": png()}


def archive(entries, stored=()):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as bundle:
        for name, value in entries:
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if name in stored else zipfile.ZIP_DEFLATED
            bundle.writestr(info, value)
    return data.getvalue()


def docx(seed, meta=True):
    """Write an Office Open XML (ECMA-376) document."""
    word = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    run = lambda text, props="": f"<w:r><w:rPr>{props}</w:rPr><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"
    lines = paragraphs(seed)
    body = (f"<w:p><w:pPr><w:jc w:val=\"center\"/></w:pPr>{run(lines[0], '<w:b/><w:sz w:val=\"32\"/>')}</w:p>"
            f"<w:p>{run(lines[1], '<w:i/>')}{run(' under ', '<w:u w:val=\"single\"/>')}{run('red', '<w:color w:val=\"FF0000\"/><w:rFonts w:ascii=\"Courier\" w:hAnsi=\"Courier\"/>')}</w:p>"
            f"<w:p><w:pPr><w:ind w:left=\"720\" w:firstLine=\"360\"/><w:spacing w:after=\"240\"/></w:pPr>{run(lines[2])}<w:r><w:tab/><w:t>tab</w:t><w:br/><w:t>line</w:t></w:r></w:p>"
            "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>a1</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>b1</w:t></w:r></w:p></w:tc></w:tr></w:tbl>")
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    core = ("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
            f"<dc:title>Docx {seed}</dc:title><dc:creator>Creator</dc:creator><cp:keywords>a, b</cp:keywords><dcterms:created xsi:type=\"dcterms:W3CDTF\">2012-03-04T05:06:07Z</dcterms:created></cp:coreProperties>")
    types = ("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/>"
             "<Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/><Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/></Types>")
    rels = (f"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"{rel}/officeDocument\" Target=\"word/document.xml\"/>"
            + ("<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" Target=\"docProps/core.xml\"/>" if meta else "") + "</Relationships>")
    document = f"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><w:document xmlns:w=\"{word}\"><w:body>{body}<w:sectPr/></w:body></w:document>"
    entries = [("[Content_Types].xml", types), ("_rels/.rels", rels), ("word/document.xml", document)] + ([("docProps/core.xml", core)] if meta else [])
    return archive(entries)


def odt(seed):
    """Write an OpenDocument 1.2 text package with the mimetype entry first and stored."""
    ns = "xmlns:office=\"urn:oasis:names:tc:opendocument:xmlns:office:1.0\" xmlns:text=\"urn:oasis:names:tc:opendocument:xmlns:text:1.0\" xmlns:style=\"urn:oasis:names:tc:opendocument:xmlns:style:1.0\" xmlns:fo=\"urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0\" xmlns:table=\"urn:oasis:names:tc:opendocument:xmlns:table:1.0\" xmlns:meta=\"urn:oasis:names:tc:opendocument:xmlns:meta:1.0\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\""
    lines = paragraphs(seed)
    styles = "<office:automatic-styles><style:style style:name=\"B\" style:family=\"text\"><style:text-properties fo:font-weight=\"bold\" fo:color=\"#0000ff\"/></style:style><style:style style:name=\"C\" style:family=\"paragraph\"><style:paragraph-properties fo:text-align=\"center\"/><style:text-properties fo:font-size=\"16pt\" fo:font-style=\"italic\"/></style:style></office:automatic-styles>"
    content = (f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><office:document-content {ns} office:version=\"1.2\">{styles}<office:body><office:text>"
               f"<text:h text:outline-level=\"1\">{escape(lines[0])}</text:h><text:p text:style-name=\"C\">{escape(lines[1])}</text:p>"
               f"<text:p>{escape(lines[2])} <text:span text:style-name=\"B\">bold</text:span><text:tab/>tab<text:line-break/>line<text:s text:c=\"3\"/>gap</text:p>"
               "<text:list><text:list-item><text:p>item</text:p></text:list-item></text:list>"
               "<table:table><table:table-column table:number-columns-repeated=\"2\"/><table:table-row><table:table-cell><text:p>a1</text:p></table:table-cell><table:table-cell><text:p>b1</text:p></table:table-cell></table:table-row></table:table>"
               "</office:text></office:body></office:document-content>")
    meta = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><office:document-meta {ns} office:version=\"1.2\"><office:meta><dc:title>Odt {seed}</dc:title><dc:creator>Creator</dc:creator><meta:keyword>kw</meta:keyword></office:meta></office:document-meta>"
    manifest = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><manifest:manifest xmlns:manifest=\"urn:oasis:names:tc:opendocument:xmlns:manifest:1.0\"><manifest:file-entry manifest:media-type=\"application/vnd.oasis.opendocument.text\" manifest:full-path=\"/\"/><manifest:file-entry manifest:media-type=\"text/xml\" manifest:full-path=\"content.xml\"/><manifest:file-entry manifest:media-type=\"text/xml\" manifest:full-path=\"meta.xml\"/></manifest:manifest>"
    return archive([("mimetype", "application/vnd.oasis.opendocument.text"), ("content.xml", content), ("meta.xml", meta), ("META-INF/manifest.xml", manifest)], stored={"mimetype"})


def wordml(seed):
    """Write a Word 2003 XML (WordprocessingML) document."""
    lines = paragraphs(seed)
    run = lambda text, props="": f"<w:r><w:rPr>{props}</w:rPr><w:t>{escape(text)}</w:t></w:r>"
    return ("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><?mso-application progid=\"Word.Document\"?>"
            "<w:wordDocument xmlns:w=\"http://schemas.microsoft.com/office/word/2003/wordml\" xmlns:o=\"urn:schemas-microsoft-com:office:office\">"
            f"<o:DocumentProperties><o:Title>WordML {seed}</o:Title><o:Author>Author</o:Author></o:DocumentProperties><w:body>"
            f"<w:p><w:pPr><w:jc w:val=\"center\"/></w:pPr>{run(lines[0], '<w:b/><w:sz w:val=\"36\"/>')}</w:p>"
            f"<w:p>{run(lines[1], '<w:i/><w:color w:val=\"00AA00\"/>')}{run(' under', '<w:u w:val=\"single\"/>')}</w:p>"
            f"<w:p><w:pPr><w:ind w:left=\"720\"/></w:pPr>{run(lines[2])}</w:p></w:body></w:wordDocument>").encode()


def webarchive(seed, image=True):
    """Write a WebKit web archive: a binary property list with a main resource and subresources."""
    main = {"WebResourceData": html(seed, "file:///pic.png" if image else None), "WebResourceFrameName": "", "WebResourceMIMEType": "text/html", "WebResourceTextEncodingName": "UTF-8", "WebResourceURL": "file:///index.html"}
    value = {"WebMainResource": main}
    if image:
        value["WebSubresources"] = [{"WebResourceData": png(), "WebResourceMIMEType": "image/png", "WebResourceURL": "file:///pic.png"}]
    return plistlib.dumps(value, fmt=plistlib.FMT_BINARY, sort_keys=True)


def compound(streams):
    """Write a version 3 compound file (MS-CFB) without a mini stream."""
    end, free, fat_mark = 0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFD
    names = sorted(streams, key=lambda name: (len(name), name.upper()))
    blobs = [streams[name].ljust(max(4096, -(-len(streams[name]) // 512) * 512), b"\0") for name in names]
    fat, sector, starts = [fat_mark], 1, []
    for blob in blobs:
        count = len(blob) // 512
        starts.append(sector)
        fat += list(range(sector + 1, sector + count)) + [end]
        sector += count
    directory_sector = sector
    fat += [end]
    fat += [free] * (128 - len(fat))

    def entry(name, kind, color, left, right, child, start, size):
        encoded = (name + "\0").encode("utf-16-le")
        return encoded.ljust(64, b"\0") + struct.pack("<HBBIII16sIQQIQ", len(encoded), kind, color, left, right, child, b"", 0, 0, 0, start, size)

    count = len(names)
    tree = [entry(name, 2, 0 if index < count - 1 else 1, index if index else free, free, free, starts[index], len(blobs[index])) for index, name in enumerate(names)]
    tree = [entry("Root Entry", 5, 1, free, free, count, end, 0)] + tree
    header = struct.pack("<8s16sHHHHH6sIIIIIIIII", bytes.fromhex("D0CF11E0A1B11AE1"), b"", 0x3E, 3, 0xFFFE, 9, 6, b"", 0, 1, directory_sector, 0, 4096, end, 0, end, 0)
    header += struct.pack("<I", 0) + struct.pack("<I", free) * 108
    directory = b"".join(tree).ljust(512, b"\0")
    return header + struct.pack("<128I", *fat) + b"".join(blobs) + directory


def doc(seed):
    """Write a Word 97 binary document (MS-DOC) with a FIB, UTF-16 text, and a piece table."""
    text = "\r".join(paragraphs(seed)).replace("\t", " ") + "\r"
    encoded = text.encode("utf-16-le")
    count = len(encoded) // 2
    position = 0x800
    clx = struct.pack("<II", 0, count) + struct.pack("<HIH", 0, position, 0)
    clx = struct.pack("<BI", 2, len(clx)) + clx
    base = struct.pack("<HHHHHHHIBBHHII", 0xA5EC, 0xC1, 0, 0x0409, 0, 0x1200, 0xBF, 0, 0, 0, 0, 0, 0, 0)
    words16 = struct.pack("<H", 14) + b"\0" * 28
    longs = [0] * 22
    longs[0], longs[3] = position + len(encoded), count
    pairs = [0] * (93 * 2)
    pairs[66], pairs[67] = 0, len(clx)
    fib = base + words16 + struct.pack("<H22i", 22, *longs) + struct.pack("<H186I", 93, *pairs) + struct.pack("<H", 0)
    stream = fib.ljust(position, b"\0") + encoded
    return compound({"WordDocument": stream, "1Table": clx})
