"""Generate seeded probes for the D-generate distinguisher."""

import itertools
import random

from cases import probe, script

SEED = 20261025
MODULE = "print('module loaded', ...)\nreturn {v = 'mod'}\n"
MAIN = "print('script', ...)\nprint(#arg, arg[0], arg[-1])\n"
OPTIONS = {
    "e": lambda rng: ["-e", rng.choice(["print('e')", "x = (x or 0) + 1 print(x)", "error('e fails')", "x =", "io.write(1, '\\n')", ""])],
    "l": lambda rng: ["-l", rng.choice(["mod", "g=mod", "missing", "string"])],
    "i": lambda rng: ["-i"],
    "v": lambda rng: ["-v"],
    "E": lambda rng: ["-E"],
    "W": lambda rng: ["-W"],
    "dashdash": lambda rng: ["--"],
    "dash": lambda rng: ["-"],
    "script": lambda rng: ["main.lua", *rng.sample(["a", "-e", "--", "-i", "b c"], rng.randrange(3))],
    "bad": lambda rng: [rng.choice(["-x", "-ix", "-vv", "-E-", "---", "-l", "-e"])],
}
STDIN = ["", "print('stdin chunk', ...)\n", "1 + 1\nprint(x)\n", "for i = 1, 2 do\nprint(i)\nend\n", "error('stdin error')\n", "warn('w')\n"]
INIT = [None, {"LUA_INIT": "print('init')"}, {"LUA_INIT": "error('init')"}, {"LUA_INIT_5_5": "x = 100"}, {"LUA_INIT": "@mod.lua"}, {"LUA_PATH": "none/?.lua"}]


def cli(rng):
    """Cover every ordered option pair and seeded longer option sequences."""
    result = []
    files = {"main.lua": MAIN, "mod.lua": MODULE}
    names = sorted(OPTIONS)
    sequences = [list(pair) for pair in itertools.product(names, repeat=2)]
    sequences += [[rng.choice(names) for _ in range(rng.randrange(3, 6))] for _ in range(120)]
    for number, sequence in enumerate(sequences):
        args = [token for name in sequence for token in OPTIONS[name](rng)]
        result.append(probe(f"cli-options/gen-{number:03d}-{'-'.join(sequence)}", args, rng.choice(STDIN), files, rng.choice(INIT)))
    return result


OPERANDS = ["0", "1", "-1", "2", "3", "7", "-7", "255", "0.5", "-0.0", "1.5", "1e308", "-1e308", "2^53", "math.maxinteger", "math.mininteger", "math.huge", "-math.huge", "(0/0)", "'10'", "'0x10'", "'1e2'", "' 3 '", "'abc'", "3.25", "0x7f", "1e-300", "nil", "true", "{}"]
BINARY = ["+", "-", "*", "/", "//", "%", "^", "&", "|", "~", "<<", ">>", "..", "==", "~=", "<", "<=", ">", ">="]
UNARY = ["-", "~", "not ", "#"]


def expression(rng, depth):
    if depth == 0 or rng.random() < 0.3:
        return rng.choice(OPERANDS)
    if rng.random() < 0.15:
        return rng.choice(UNARY) + "(" + expression(rng, depth - 1) + ")"
    return "(" + expression(rng, depth - 1) + " " + rng.choice(BINARY) + " " + expression(rng, depth - 1) + ")"


SNIPPETS = [
    "local x = 1 + 2 * 3 return x", "for i = 1, 10 do if i % 2 == 0 then goto c end ::c:: end",
    "local t = {1, 2, [3] = 3, x = {y = 'z'}} return #t", "function f(a, ...) return a, ... end return f(1, 2)",
    "while true do break end repeat local a = 1 until a", "local s = [[long]] .. \"esc\\n\" .. 'q' return s",
    "global g <const> = 5 return g", "local c <close> = nil return 0x1p4 // 3", "return function (...t) return t.n end",
    "if a then b() elseif c then d = {e = f} else g = h:i(j) end", "local a <const>, b = 1, 2 return a ~ b << 1",
]


def mutate(rng, text):
    text = list(text)
    for _ in range(rng.randrange(1, 4)):
        action = rng.randrange(3)
        position = rng.randrange(len(text) + 1)
        if action == 0 and text:
            del text[min(position, len(text) - 1)]
        elif action == 1:
            text.insert(position, rng.choice("()[]{}=.,;:'\"<>~#-+*/%^\\ \n0123456789abcxyz@$!?\t\0\xff"))
        elif text:
            text[min(position, len(text) - 1)] = rng.choice("=([{'\"x9.:;<")
    return "".join(text)


def quote(text):
    return "'" + "".join(c if c.isalnum() or c in " ()[]{}=.,;:<>~#-+*/%^_!?$@" else f"\\{ord(c):03d}" for c in text) + "'"


SHOW = "local function show(...) local r = table.pack(...) for k = 1, r.n do if type(r[k]) == 'table' or type(r[k]) == 'function' then r[k] = type(r[k]) end end print(table.unpack(r, 1, r.n)) end\n"


def core(rng):
    result = []
    for number in range(40):
        lines = [f"show({index}, pcall(function () return {expression(rng, 3)} end))" for index in range(25)]
        result.append(script(f"arithmetic/gen-expressions-{number:02d}", SHOW + "\n".join(lines) + "\n"))
    for number in range(30):
        lines = [f"show({index}, load({quote(mutate(rng, rng.choice(SNIPPETS)))}, '=gen'))" for index in range(20)]
        result.append(script(f"syntax-errors/gen-mutations-{number:02d}", SHOW + "\n".join(lines) + "\n"))
    alphabet = "0123456789abcdefxXpPeE.+- \t\n"
    for number in range(15):
        values = ["".join(rng.choice(alphabet) for _ in range(rng.randrange(1, 12))) for _ in range(30)]
        lines = [f"print({quote(value)}, tonumber({quote(value)}), tonumber({quote(value)}, {rng.randrange(2, 37)}), math.tointeger({quote(value)}))" for value in values]
        lines += [f"print(string.format('%.17g', {rng.uniform(-1e20, 1e20)!r}), {rng.uniform(-1e5, 1e5)!r}, {rng.randrange(-2**63, 2**63)}, 2^{rng.randrange(-1100, 1100)})" for _ in range(10)]
        result.append(script(f"coercion/gen-numbers-{number:02d}", "\n".join(lines) + "\n"))
    for number in range(10):
        lines = []
        for index in range(20):
            items = [rng.choice(["nil", "1", "'x'", "{}", "k = 1", "[2] = 2", "[0] = 0", "[1.0] = 'f'"]) for _ in range(rng.randrange(8))]
            lines.append(f"do local t = {{{', '.join(items)}}} local n = 0 for _ in pairs(t) do n = n + 1 end show({index}, #t, n, t[1], t[2], rawlen(t)) end")
        result.append(script(f"tables/gen-constructors-{number:02d}", SHOW + "\n".join(lines) + "\n"))
    return result


SUBJECTS = ["hello world", "aaa bbb", "x=1, y=22", "(a(b)c)", "  trim  ", "", "\0\1\2", "ÄÖÜ äöü", "%%d", "a.b-c+d*e?f[g]h^i$j"]
PIECES = ["a", "b", ".", "%a", "%d", "%s", "%w", "%p", "%u", "%l", "%x", "%c", "%A", "[ab]", "[^a]", "[a-z]", "[%d%s]", "%b()", "%f[%w]", "(", ")", "()", "*", "+", "-", "?", "^", "$", "%1", "%", "[", "]"]
FORMATS = ["d", "i", "x", "X", "o", "c", "e", "E", "f", "g", "G", "a", "A", "s", "q", "%"]
PACK = ["b", "B", "h", "H", "i", "I", "l", "L", "j", "J", "T", "f", "d", "n", "i3", "I7", "s1", "s2", "z", "c3", "x", "<", ">", "=", "!", "!2", "Xi4"]
DATES = list("aAbBcCdDeFgGhHIjmMnprRStTuUVwWxXyYzZ%") + ["Ec", "Ox", "q", ""]


def extended(rng):
    result = []
    for number in range(30):
        lines = []
        for index in range(20):
            pattern = "".join(rng.choice(PIECES) for _ in range(rng.randrange(1, 5)))
            subject = rng.choice(SUBJECTS)
            call = rng.choice(["string.find(s, p)", "string.match(s, p)", "string.gsub(s, p, '<%0>')", "string.find(s, p, 2, true)", "select('#', string.gsub(s, p, '%%'))", "(function () local r = {} for a, b in string.gmatch(s, p) do r[#r + 1] = tostring(a) .. tostring(b) end return table.concat(r, '|') end)()"])
            lines.append(f"do local s, p = {quote(subject)}, {quote(pattern)} print({index}, pcall(function () return {call} end)) end")
        result.append(script(f"patterns/gen-{number:02d}", "\n".join(lines) + "\n"))
    for number in range(30):
        lines = []
        for index in range(20):
            spec = "%" + "".join(rng.sample("-+ #0", rng.randrange(3))) + rng.choice(["", "1", "5", "12", "99", "100"]) + rng.choice(["", ".", ".0", ".3", ".20", ".99"]) + rng.choice(FORMATS)
            value = rng.choice(["0", "-1", "255", "3.0", "3.5", "-0.0", "1e300", "1/0", "-1/0", "math.mininteger", "math.maxinteger", "'text'", "'a\\0b'", "''", "nil", "true", "2^63", "0.1", "65"])
            lines.append(f"print({index}, {quote(spec)}, pcall(string.format, {quote(spec)}, {value}))")
        result.append(script(f"string-format/gen-{number:02d}", "\n".join(lines) + "\n"))
    for number in range(20):
        lines = ["local function hex(s) return (s:gsub('.', function (c) return string.format('%02x', c:byte()) end)) end"]
        for index in range(15):
            fmt = " ".join(rng.choice(PACK) for _ in range(rng.randrange(1, 5)))
            values = ", ".join(rng.choice(["0", "1", "-1", "127", "-128", "255", "65535", "2^31", "-2^31", "math.maxinteger", "1.5", "'ab'", "''", "'xyz\\0'"]) for _ in range(5))
            lines.append(f"do local ok, s = pcall(string.pack, {quote(fmt)}, {values}) print({index}, {quote(fmt)}, ok, ok and hex(s) or s, pcall(string.packsize, {quote(fmt)})) if ok then print(pcall(string.unpack, {quote(fmt)}, s)) end end")
        result.append(script(f"string-pack/gen-{number:02d}", "\n".join(lines) + "\n"))
    for number in range(15):
        lines = []
        for index in range(20):
            data = bytes(rng.choice([rng.randrange(128), rng.randrange(128, 256), 0xED, 0xF4, 0xC0, 0x80]) for _ in range(rng.randrange(1, 10)))
            text = "".join(f"\\{byte:03d}" for byte in data)
            lax = rng.choice(["true", "false"])
            lines.append(f"do local s = '{text}' print({index}, utf8.len(s), utf8.len(s, 1, -1, {lax}), pcall(utf8.codepoint, s, 1, -1, {lax}), utf8.offset(s, 2), pcall(function () local r = {{}} for p, c in utf8.codes(s, {lax}) do r[#r + 1] = p .. ':' .. c end return table.concat(r, ',') end)) end")
        result.append(script(f"utf8/gen-{number:02d}", "\n".join(lines) + "\n"))
    for number in range(15):
        size = rng.randrange(1, 60)
        values = ", ".join(str(rng.randrange(-20, 20)) for _ in range(size))
        result.append(script(f"table-library/gen-sort-{number:02d}", f"local t = {{{values}}}\nlocal n = 0\ntable.sort(t, function (a, b) n = n + 1 return a > b end)\nprint(table.concat(t, ' '), n)\nlocal r = {{}}\nfor i = 1, #t do r[i] = {{k = t[i] % 3, i = i}} end\ntable.sort(r, function (a, b) return a.k < b.k end)\nfor i = 1, #r do io.write(r[i].i, ' ') end print()\n"))
    for number in range(10):
        lines = []
        for index in range(20):
            fmt = "".join("%" + rng.choice(DATES) + rng.choice(["", " ", "-", "/"]) for _ in range(rng.randrange(1, 5)))
            when = rng.randrange(-2**31, 2**33)
            lines.append(f"print({index}, pcall(os.date, {quote(rng.choice(['!', '']) + fmt)}, {when}))")
            lines.append(f"print(pcall(os.time, {{year = {rng.randrange(1800, 2400)}, month = {rng.randrange(-20, 30)}, day = {rng.randrange(-40, 70)}, hour = {rng.randrange(-30, 50)}, min = {rng.randrange(-100, 100)}, sec = {rng.randrange(-100, 100)}}}))")
        result.append(script(f"os-library/gen-dates-{number:02d}", "\n".join(lines) + "\n"))
    for number in range(10):
        lines = [f"math.randomseed({rng.randrange(-2**63, 2**63)}, {rng.randrange(2**63)})"]
        for index in range(20):
            low = rng.randrange(-1000, 1000)
            fn = rng.choice(["sin", "cos", "tan", "asin", "acos", "atan", "exp", "log", "sqrt", "floor", "ceil", "abs", "modf", "fmod", "ult", "tointeger"])
            arg = rng.choice([str(low), repr(rng.uniform(-10, 10)), "2^53", "-0.0", "math.huge", "math.mininteger"])
            second = rng.choice(["", ", 2", ", -3", ", 0.5"]) if fn in ("atan", "log", "fmod", "ult") else ""
            lines.append(f"print({index}, pcall(math.{fn}, {arg}{second}), math.random({low}, {low + rng.randrange(0, 10**6)}), string.format('%.17g', math.random()))")
        result.append(script(f"math-library/gen-{number:02d}", "\n".join(lines) + "\n"))
    return result


def reports():
    rng = random.Random(SEED)
    return {"generate-cli": cli(rng), "generate-core": core(rng), "generate-extended": extended(rng)}
