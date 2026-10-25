"""Generate deterministic Lua 5.5.1 scenarios for the replay, surface, and generate distinguishers."""

import base64
import random


def encode(data):
    return base64.b64encode(data if isinstance(data, bytes) else data.encode()).decode("ascii")


def probe(identity, args, stdin="", files=None, env=None):
    item = {"id": identity, "args": list(args), "stdin_b64": encode(stdin)}
    if files:
        item["files"] = {name: encode(value) for name, value in files.items()}
    if env:
        item["env"] = env
    return item


def script(identity, source, *args, stdin="", files=None, env=None, pre=()):
    """Run main.lua with the given source, options before it, and arguments after it."""
    return probe(identity, [*pre, "main.lua", *args], stdin, {"main.lua": source, **(files or {})}, env)


CORE = [
    # The language core and the base library.
    ("lexer/numerals", r"""
print(0x10, 0xA.8p1, 1e2, .5, 3., 0x.1, 0X1P-2, 1E+2, 9007199254740993)
print(0xffffffffffffffff, 0x7fffffffffffffff, 9223372036854775807, 9223372036854775808)
print(1e309, -1e309, -0.0, 0.0, 100, 100.0, 1e15, 1e16, 123456789012345678)
print(math.type(1), math.type(1.0), math.type(0x10), math.type(1e2), math.type("1"))
"""),
    ("lexer/strings", r"""
local s = "\a\b\f\n\r\t\v\\\"\'"
print(s:byte(1, -1))
print("\x41\65\066\u{48}\u{20AC}\z
       continued", #"\u{7FFFFFFF}", ("\u{7FFFFFFF}"):byte(1, -1))
print([==[
first newline skipped ]] ]=] ]==], [[a
b]], '\0' == "\x00", #"a\0b")
"""),
    ("lexer/comments", "#!/usr/bin/env lua\n-- line\n--[[ block\n]] print(1) --[==[ long\n]] ]==] print(2)\n--[ not long\nprint(3)\n"),
    ("syntax-errors/messages", r"""
local sources = {
  "x = = 1", "local 1 = 2", "if x then", "for i = 1 do end", "x = 'unfinished",
  "x = [[unfinished", "--[[ unfinished", "x = \"\\q\"", "x = \"\\x4\"", "x = \"\\u{110000000}\"",
  "x = \"\\300\"", "x = 3x", "x = 0x", "x = 1e", "x = 1..2", "return return", "f(", "a.b:c = 1",
  "local function end", "goto nowhere", "::a:: ::a::", "break", "do local x <foo> = 1 end",
  "local x <const> = 1; x = 2", "x = }", "x = '\n'", "x = ~= 1", "local t = {1 2}", "(1)", "a, b",
  "x = 1 + ", "function f(a,) end", "function f(..., a) end", "local a <close>, b <close> = 1, 2",
  "for i = 1, 2 do i = 3 end", "x = @", "x = $", "return 1 1", "local x = 08.5e", "a = b = c",
  string.rep("(", 300) .. "1" .. string.rep(")", 300),
}
for i, src in ipairs(sources) do print(i, load(src, "=src")) end
"""),
    ("numbers/arithmetic", r"""
print(7 // 2, -7 // 2, 7 // -2, 7.0 // 2, -7 // 2.0, 7 % 3, -7 % 3, 7 % -3, -7 % -3, 7.5 % 2, -7.5 % 2)
print(5.3 % -2, 1 / 0, -1 / 0, 0/0 ~= 0/0, 2^10, 2^0.5, (-8)^(1/3), 10 / 2, 3 * 1.0, -(-3))
print(math.maxinteger + 1 == math.mininteger, math.mininteger - 1, math.maxinteger * 2, -math.mininteger)
print(math.mininteger // -1, math.mininteger % -1, 5 // 0.0, -5 // 0.0, 0/0 == 0/0, 5 % math.huge, -5 % math.huge)
print(pcall(function () return 1 // 0 end))
print(pcall(function () return 1 % 0 end))
print(1e100, 2^53, 2^63, -2^63, 0.1, 1/3, -1/3, 3.14159265358979, 1e-310, 5e-324, 2^-1074)
print(255 // 1, 3 == 3.0, math.maxinteger + 0.0 == math.maxinteger, 2^53 == 2^53 + 1, math.maxinteger < math.huge)
print(1 < 1.5, -0.0 == 0.0, math.mininteger <= -2^63, math.maxinteger + 0.0, 9007199254740993 < 9007199254740992.0)
"""),
    ("bitwise/operators", r"""
print(5 & 3, 5 | 3, 5 ~ 3, ~0, ~5, 1 << 63, 1 << 64, 1 << -1, -1 >> 1, -1 >> 64, 2 >> -1, 3.0 | 0, 0xF0 ~ 0xFF)
print(pcall(function () return 2.5 | 0 end))
print(pcall(function () return "2.5" | 0 end))
print(pcall(function () return "a" | 0 end))
print(pcall(function () return {} & 1 end))
print(pcall(function () return 2^63 | 0 end))
print(math.mininteger >> 63, math.maxinteger << 1, 1 << 62, 1e3 | 0)
print(pcall(function () return "3" | 0 end))
print(pcall(function () return "0x10" & 0xff end))
"""),
    ("coercion/strings", r"""
print("10" + 1, "3.0" + 1, "0x10" + 0, " 5 " * 2, "1e2" // 1, 10 .. 20, 1.5 .. "", -0.0 .. "", 2^63 .. "")
print(pcall(function () return "abc" + 1 end))
print(pcall(function () local a = "x"; return a * 2 end))
print(pcall(function () return {} .. "x" end))
print(pcall(function () return 1 .. nil end))
print("10" == 10, "abc" < "abd", "Z" < "a", "" < "a", "a\0b" < "a\0c", "10" < "9")
print(pcall(function () return 1 < "2" end))
print(pcall(function () return {} < {} end))
print(pcall(function () return nil > 1 end))
"""),
    ("control-flow/loops", r"""
local out = {}
for i = 1, 3 do out[#out+1] = i end
for i = 3, 1, -1 do out[#out+1] = i end
for i = 1, 2, 0.5 do out[#out+1] = i end
for i = math.maxinteger - 2, math.maxinteger do out[#out+1] = i end
for i = math.mininteger, math.mininteger + 2, 1 do out[#out+1] = i end
for i = 1, 0 do out[#out+1] = "never" end
for i = 1.0, 3 do out[#out+1] = i end
for i = 1, 3.5 do out[#out+1] = i end
print(table.concat(out, " "))
local n = 0
while true do n = n + 1; if n > 4 then break end end
repeat local k = n; n = n - 1 until k < 3
print(n)
print(pcall(function () for i = 1, 10, 0 do end end))
print(pcall(function () for i = "a", 2 do end end))
print(pcall(function () for i = 1, {} do end end))
print(pcall(function () for i = 1, 2, nil do end end))
for i = 3, 1 do print("x") end
if nil then print(1) elseif false then print(2) elseif 0 then print(3) else print(4) end
"""),
    ("control-flow/generic-for", r"""
local function iter(s, c) if c < s then return c + 1, c * 2 end end
for a, b in iter, 3, 0 do io.write(a, ":", b, " ") end print()
local closed = false
do
  local mt = {__close = function () closed = true end}
  for x in function (s, c) if c < 2 then return c + 1 end end, nil, 0, setmetatable({}, mt) do io.write(x, " ") end
end
print(closed)
for i, v in ipairs({1, 2, nil, 4}) do io.write(i, "=", v, " ") end print()
print(pcall(function () for x in 1 do end end))
"""),
    ("goto/labels", r"""
for i = 1, 3 do
  for j = 1, 3 do
    if j == 2 then goto continue end
    io.write(i, j, " ")
    ::continue::
  end
end
print()
do goto skip; print("no") ::skip:: end
local k = 0
::top:: k = k + 1 if k < 3 then goto top end
print(k)
print(load("goto x", "=g"))
print(load("do goto l end local y ::l:: print(y)", "=g"))
print(load("::l:: ::l::", "=g"))
print(load("do ::l:: end goto l", "=g"))
print(load("repeat local x; goto c; ::c:: until x", "=g") ~= nil)
"""),
    ("functions/closures", r"""
local function counter() local c = 0 return function () c = c + 1 return c end end
local a, b = counter(), counter()
print(a(), a(), b(), a())
local fs = {}
for i = 1, 3 do fs[i] = function () return i end end
print(fs[1](), fs[2](), fs[3]())
local function fact(n) if n <= 1 then return 1 end return n * fact(n - 1) end
print(fact(20), fact(21), fact(25.0))
local function loop(n) if n == 0 then return "done" end return loop(n - 1) end
print(loop(1000000))
local t = {x = 5}
function t:get(y) return self.x + y end
function t.static(y) return y end
print(t:get(1), t.get(t, 2), t.static(3), ("x"):rep(3), #"abc", (("x")))
print(pcall(function () local function r() return 1 + r() end return r() end))
print(select("#", (function () return 1, 2, 3 end)()), ((function () return 1, 2, 3 end)()))
"""),
    ("varargs/select", r"""
local function f(...) return select("#", ...), ... end
print(f())
print(f(nil, nil))
print(select(2, "a", "b", "c"), select(-1, "a", "b", "c"), select(-3, "a", "b", "c"))
print(pcall(select, 0, 1))
print(pcall(select, -4, 1, 2, 3))
local function g(...t) return t.n, t[1], t[2], #t end
print(g(10, nil, 30))
local function h(a, ...) local x, y = ... return a, x, y end
print(h(1), h(1, 2, 3))
print(table.unpack({1, 2, 3}), table.pack(1, nil, 3).n, (table.unpack({1, 2, 3})))
local t = {f(1, 2), f(3, 4)}
print(#t, t[1], t[2], t[3], t[4])
print(pcall(load, "function f(...t) t = 1 end"))
"""),
    ("tables/constructors", r"""
local t = {1, 2, 3; x = 1, ["y"] = 2, [10] = 10, 4,}
print(#t, t[4], t.x, t.y, t[10])
print(#{1, nil, 3}, #{nil, nil, 3}, #{n = 1}, #"", #{1, 2, 3, nil})
local k = {}
k[1.0] = "one"; k[2^53] = "big"
print(k[1], k[2^53 | 0], math.type(next(k)), rawlen({1, 2}), rawlen("abcd"))
print(pcall(function () local x = {}; x[nil] = 1 end))
print(pcall(function () local x = {}; x[0/0] = 1 end))
print(rawget({}, nil), ({})[0/0], next({}), type(next), next({5}))
local arr = {}
for i = 1, 10 do arr[i] = i * i end
arr[5] = nil
local keys = {}
for k2, v in pairs({10, 20, 30}) do keys[#keys + 1] = k2 .. "=" .. v end
print(table.concat(keys, ","))
local named = {}
for k2 in pairs({alpha = 1, beta = 2, gamma = 3, delta = 4}) do named[#named + 1] = k2 end
table.sort(named)
print(table.concat(named, ","))
"""),
    ("metatables/events", r"""
local V = {}
V.__index = V
V.__add = function (a, b) return setmetatable({v = a.v + b.v}, V) end
V.__sub = function (a, b) return "sub" end
V.__mul = function (a, b) return "mul" end
V.__div = function () return "div" end
V.__mod = function () return "mod" end
V.__pow = function () return "pow" end
V.__unm = function (a) return "unm" end
V.__idiv = function () return "idiv" end
V.__band = function () return "band" end
V.__bor = function () return "bor" end
V.__bxor = function () return "bxor" end
V.__shl = function () return "shl" end
V.__shr = function () return "shr" end
V.__bnot = function () return "bnot" end
V.__concat = function (a, b) return "concat" end
V.__len = function () return 42 end
V.__eq = function () return true end
V.__lt = function () return true end
V.__le = function () return false end
V.__call = function (self, a, b) return "call", a, b end
V.__tostring = function (self) return "V(" .. tostring(self.v) .. ")" end
V.__name = "Vector"
local a, b = setmetatable({v = 1}, V), setmetatable({v = 2}, V)
print(tostring(a + b), a - b, a * 1, 1 / a, a % 1, a ^ 2, -a, a // 1, a & 1, 1 | a, a ~ a, a << 1, a >> 1, ~a)
print(a .. "x", "x" .. a, 1 .. a, #a, a == b, a ~= b, a < b, a <= b, a > b, a >= b, a(1, 2))
print(a == setmetatable({}, {}), rawequal(a, b), rawlen(a))
local prox = setmetatable({}, {__index = function (t, k) return k .. "!" end, __newindex = function (t, k, v) rawset(t, k, v * 2) end})
prox.x = 5
print(prox.x, prox.y, rawget(prox, "y"))
local chain = setmetatable({}, {__index = setmetatable({a = 1}, {__index = {b = 2}})})
print(chain.a, chain.b, chain.c)
local locked = setmetatable({}, {__metatable = "locked"})
print(getmetatable(locked), pcall(setmetatable, locked, {}))
print(getmetatable("").__index == string, ("abc"):upper(), #getmetatable("").__index.format("%5s", "x"))
local named = setmetatable({}, {__name = "MyType"})
print(pcall(function () return named + 1 end))
print(pcall(function () return #named < 1, named < 1 end))
print((tostring(named):gsub("0x%x+", "ADDR")))
"""),
    ("metatables/call-chain", r"""
local f = function (...) return select("#", ...) end
for depth = 1, 17 do
  local obj = f
  for i = 1, depth do obj = setmetatable({}, {__call = obj}) end
  print(depth, pcall(obj, "x"))
end
"""),
    ("to-be-closed/order", r"""
local function closer(name) return setmetatable({}, {__close = function (o, e) print("close", name, e) end}) end
do
  local a <close> = closer("a")
  local b <close> = closer("b")
  local c <close> = nil
  local d <close> = false
  print("body")
end
print(pcall(function ()
  local x <close> = closer("x")
  error("boom")
end))
print(pcall(function ()
  local y <close> = setmetatable({}, {__close = function () error("in close") end})
  local z <close> = closer("z")
  error("first")
end))
print(pcall(function () local w <close> = {} end))
print(pcall(function () local w <close> = 42 end))
local function gen()
  local r <close> = closer("ret")
  return "returned"
end
print(gen())
"""),
    ("const/attributes", r"""
local x <const> = 10
local s <const> = "str"
print(x + 1, s .. "!")
print(load("local a <const> = 1; a = 2", "=c"))
print(load("local a <const> = 1; return function () a = 2 end", "=c"))
print(load("local a <unknown> = 1", "=c"))
print(load("local a <close>, b <close> = 1, 2", "=c"))
print(load("for i = 1, 2 do i = 3 end", "=c"))
print(load("for k, v in pairs{} do k = 1 end", "=c"))
print(load("for i = 1, 2 do local i = i + 1 end", "=c") ~= nil)
"""),
    ("global-declarations/statements", r"""
do
  global x = 10
  global <const> K = 42
  global function gf() return "gf" end
  global print, _G
  print(x, K, gf(), _G.x, _G.K)
end
local function show(src)
  local f, msg = load(src, "=g")
  if f then print("ok", pcall(f)) else print("error", msg) end
end
show("global a; return print")
show("global y; y = 1; return y")
show("global <const> C = 1; C = 2")
show("global a; b = 1")
show("global *; b = 1; return b")
show("global <const> *; b = 1")
show("local global = 1; return global")
show("global a, b <const>, c = 1, 2, 3; return a, b, c")
show("global none; return undeclared")
show("global q = 5; return q")
show("global <close> q = 5")
show("do global z end; z = 1; return z")
show("global function gf2() return 'g' end return gf2()")
show("global <const> *; local function f() return print end return f() == print")
show("global x <const> = 1; global x = 2; return x")
show("local x = 1; global x; x = 3; return x")
show("global *; global <const> pi; return pi == nil")
"""),
    ("error-handling/pcall", r"""
print(pcall(error))
print(pcall(error, nil))
print(pcall(error, "msg"))
print(pcall(error, "msg", 0))
print(pcall(error, "msg", 2))
print(type(select(2, pcall(error, {code = 1}))))
print(select("#", pcall(error)))
local function lvl() error("deep", 2) end
print(pcall(function () lvl() end))
print(xpcall(function () error("x") end, function (m) return "handled: " .. m end))
print(xpcall(function (a, b) return a + b end, print, 3, 4))
print(xpcall(function () error("x") end, function (m) error("y") end))
print(pcall(assert, false))
print(pcall(assert, nil, "custom"))
print(pcall(assert, 1, 2, 3))
print(pcall(assert))
print(pcall(error, setmetatable({}, {__tostring = function () return "TS" end})))
print(pcall(pcall))
print(pcall(xpcall, print))
print(string.format("%q", select(2, pcall(error, 12))))
"""),
    ("error-handling/messages", r"""
local function try(f) print(select(2, pcall(f))) end
try(function () return undefinedvar.x end)
try(function () local t; return t.x end)
try(function () local t = {}; return t.a.b end)
try(function () local t = {}; t.a.b = 1 end)
try(function () return ("x")() end)
try(function () local t = {}; t:nomethod() end)
try(function () local up; return (function () return up.x end)() end)
try(function () return math.nofunc() end)
try(function () return #nil end)
try(function () return -{} end)
try(function () local t = {}; return t.x + 1 end)
try(function () return 1 + true end)
try(function () return ({}) .. "x" end)
try(function () string.rep() end)
try(function () ("x"):rep({}) end)
try(function () table.insert(nil, 1) end)
try(function () setmetatable(1, {}) end)
try(function () return math.floor("x") end)
try(function () return ipairs() end)
try(function () string.char(256) end)
try(function () string.rep("x", -1, {}) end)
try(function () local a = {}; a[1][2] = 3 end)
try(function () tostring() end)
try(function () return io.open("x", "z") end)
try(function () return 1 < {} end)
try(function () return {} <= 1 end)
try(function () error() end)
try(function () local x <close> = 1 end)
"""),
    ("base-library/conversions", r"""
print(tonumber("0x1p4"), tonumber("  10  "), tonumber("10", 2), tonumber("zz", 36), tonumber("8", 8), tonumber(""))
print(tonumber("1e"), tonumber("0x"), tonumber(" 0x10 "), tonumber("1 2"), tonumber("inf"), tonumber("nan"), tonumber("-0x8000000000000000"))
print(tonumber("7fffffffffffffff", 16), tonumber("ffffffffffffffff", 16), tonumber("-ff", 16), tonumber("1.5", 10), tonumber(12), tonumber("\t3\n"))
print(pcall(tonumber), pcall(tonumber, "10", 1), pcall(tonumber, "10", 37), pcall(tonumber, 10, 16))
print(tostring(1e100), tostring(-0.0), tostring(2^63), tostring(nil), tostring(true), tostring(12), tostring(1.5e300 * 1e10))
print(type(nil), type(1), type("s"), type({}), type(print), type(type), type(coroutine.create(print)), type(io.stdout))
print(pcall(type))
print(rawequal(1, 1.0), rawequal("a", "a"), rawequal({}, {}), rawlen({1, 2, nil, 4}) >= 2, select("#", rawget({}, 1)))
print(_VERSION, _G._G == _G, _ENV == _G, #arg, arg[0])
print(math.tointeger(3.0), math.tointeger(3.5), math.tointeger("8"), math.tointeger(2^63), math.tointeger(-2^63))
print(string.format("%.17g", tonumber("0.1")), tonumber("1e400"), tonumber("-1e400"), tonumber("0x1P+1024"), tonumber(".5e1"))
print(tonumber("9223372036854775808"), math.type(tonumber("9223372036854775807")), tonumber("1" .. string.rep("0", 30)))
"""),
    ("base-library/iteration", r"""
local t = setmetatable({}, {__pairs = function (t) return function (_, k) if not k then return 1, "one" end end, t, nil end})
for k, v in pairs(t) do print(k, v) end
local ip = setmetatable({}, {__index = function (t, i) if i <= 3 then return i * 10 end end})
for i, v in ipairs(ip) do io.write(i, "=", v, " ") end print()
print(next({}, nil), pcall(next, {}, "nokey"))
local seen = 0
for k in pairs({1, 2, 3, a = 1, b = 2}) do seen = seen + 1 end
print(seen)
local m = {}
for i = 1, 5 do m[i] = i end
for k in pairs(m) do m[k] = nil end
print(next(m))
print(pcall(ipairs), pcall(pairs))
print(select("#", ipairs({})), select("#", pairs({})))
"""),
    ("load/chunks", r"""
print(load("return 1 + 1")())
print(load("syntax error here"))
print(load("return ...", "=name")(1, 2))
local parts = {"return ", "10 ", "* 2"}
local i = 0
print(load(function () i = i + 1 return parts[i] end)())
print(type(load(function () return nil end)))
print(load(function () return {} end))
print(load(function () error("reader") end))
local env = {y = 5}
print(load("return y", "c", "t", env)())
print(load("x = 1", "=c", "t", env)(), env.x, x)
print(load("return 1", "=c", "b"))
print(load("\27Lua", "=c", "t"))
print(load("return 1", "@file.lua") and "ok", load("error('e')", "@file.lua") ~= nil)
print(pcall(load("error('e')", "@file.lua")))
print(pcall(load("error('e')", "=custom")))
print(pcall(load("error('e')", "literal source text")))
print(pcall(load("\n\nerror('e')", string.rep("x", 100))))
print(dofile("lib.lua"), loadfile("lib.lua")(), loadfile("missing.lua"))
print(pcall(dofile, "missing.lua"))
print(loadfile("lib.lua", "t", {})())
print(loadfile("bad.lua"))
""", {"lib.lua": "return 'from lib', ...", "bad.lua": "return +"}),
    ("cli-options/basic", None, ["-e", "print(1 + 1)"]),
    ("cli-options/multiple-e", None, ["-e", "x = 10", "-e", "print(x * 2)"]),
    ("cli-options/version", None, ["-v"]),
    ("cli-options/version-and-e", None, ["-v", "-e", "print('after')"]),
    ("cli-options/unknown", None, ["-x"]),
    ("cli-options/missing-e", None, ["-e"]),
    ("cli-options/missing-l", None, ["-l"]),
    ("cli-options/bad-e", None, ["-e", "x ="]),
    ("cli-options/runtime-e", None, ["-e", "error('in e')"]),
    ("cli-options/double-dash", None, ["--", "-e"]),
    ("cli-options/combined", None, ["-vx"]),
    ("cli-options/dash-dash-only", None, ["--"]),
    ("cli-stdin/dash", None, ["-", "a", "b"], "print('stdin', ...)\nprint(arg[0], arg[1], arg[-1])\n"),
    ("cli-stdin/default", None, [], "print(10)\nprint(2)\n"),
    ("cli-stdin/error", None, ["-"], "local x = 1\nerror('e')\n"),
    ("cli-stdin/syntax", None, ["-"], "x = = 1\n"),
    ("cli-arguments/table", r"""
for i = -3, #arg do print(i, arg[i]) end
print(select("#", ...), ...)
""", ["a", "b c", ""]),
    ("exit-status/error", "local x = nil\nprint('before')\nx.y = 1\n"),
    ("exit-status/os-exit", "io.write('partial') os.exit(3)"),
    ("exit-status/os-exit-true", "os.exit(true)"),
    ("exit-status/os-exit-false", "os.exit(false)"),
    ("exit-status/os-exit-float", "os.exit(7.0)"),
    ("exit-status/os-exit-close", "local x <close> = setmetatable({}, {__close = function () print('closed') end}) os.exit(0, true)"),
    ("exit-status/os-exit-noclose", "local x <close> = setmetatable({}, {__close = function () print('closed') end}) os.exit(0)"),
    ("exit-status/missing-script", None, ["nofile.lua"]),
    ("error-reporting/traceback", r"""
local function inner() error("boom") end
local t = {}
function t.field() inner() end
function t:method() t.field() end
local function outer() return t:method() end
outer()
"""),
    ("error-reporting/table-error", "error({})"),
    ("error-reporting/tostring-error", "error(setmetatable({}, {__tostring = function () return 'custom object' end}))"),
    ("error-reporting/nil-error", "error(nil)"),
    ("error-reporting/number-error", "error(42)"),
    ("error-reporting/syntax-file", "x = = 1"),
    ("error-reporting/metamethod", "local t = setmetatable({}, {__add = function (a, b) return a.x.y end})\nlocal r = t + 1\n"),
    ("error-reporting/iterator", "for k in function () error('it') end do end"),
    ("error-reporting/deep", "local function r(n) if n == 0 then error('bottom') end r(n - 1) end r(40)"),
    ("error-reporting/tail", "local function a() error('tail') end local function b() return a() end b()"),
    ("error-reporting/coroutine", "local co = coroutine.wrap(function () error('in co') end) co()"),
    ("error-reporting/stack-overflow", "local function f() return 1 + f() end f()"),
]


EXTENDED = [
    ("string-library/basics", r"""
print(("abc"):rep(3), ("ab"):rep(3, ","), ("x"):rep(0), ("x"):rep(-1), ("x"):rep(1, "sep"))
print(("hello"):sub(2), ("hello"):sub(-3), ("hello"):sub(2, -2), ("hello"):sub(0), ("hello"):sub(10), ("hello"):sub(-100, 2), ("hello"):sub(3, 2))
print(("ABC"):byte(), ("ABC"):byte(-1), ("ABC"):byte(1, -1), ("ABC"):byte(10), string.char(72, 105), string.char())
print(("MiXeD 123"):upper(), ("MiXeD 123"):lower(), ("abc"):reverse(), (""):reverse(), ("a\0b"):len(), #("\0\0\0"))
print(math.maxinteger, ("x"):sub(math.mininteger, math.maxinteger), ("abc"):sub(2.0, 3))
print(pcall(string.rep, "x", math.maxinteger // 2, "yy"))
print(pcall(string.char, -1))
print(pcall(string.sub))
print(pcall(string.sub, "x", 1.5))
print(pcall(string.byte, "abc", 1, 1e10))
print(("%d"):format(3), string.len(123), string.upper(12.5))
"""),
    ("string-format/specifiers", r"""
local f = string.format
print(f("%d %5d %-5d| %05d %+d % d %i", 1, 2, 3, 4, 5, 6, 7))
print(f("%x %X %#x %#X %o %#o %c%c", 255, 255, 255, 255, 8, 8, 72, 105))
print(f("%e %E %.3e %10.2e", 12345.678, 0.000123, 1, -1))
print(f("%f %.0f %.10f %10.3f %-10.3f| %+.2f", 1/3, 2.5, 1/3, math.pi, math.pi, 1))
print(f("%g %G %g %g %g %.3g %#g", 1e20, 1e-20, 100000, 1000000, 0.0001, math.pi, 1))
print(f("%a %A %a", 1, 0.5, -0.1))
print(f("%s %10s %-10s| %.2s %s %s", "str", "right", "left", "truncate", 12, 1.5))
print(f("%s %s %s", nil, true, setmetatable({}, {__tostring = function () return "TS" end})))
print(f("%%"), f("%5.1s|", "abc"), f("%.0s|", "abc"))
print(f("%d", 3.0), pcall(f, "%d", 3.5))
print(pcall(f, "%d", "3.5"))
print(f("%d %s", "10", 10), f("%x", -1), f("%5.2f%%", 99.5))
print(f("%f %f %f %e", 1/0, -1/0, 1e300, 1e300))
print(f("%.99f", 1):sub(1, 20), #f("%99.99f", 1))
print(pcall(f, "%100d", 1))
print(pcall(f, "%y", 1))
print(pcall(f, "%", 1))
print(pcall(f, "%d"))
print(pcall(f, "%10q", "x"))
print(pcall(f, "%ld", 1))
print(pcall(f, "%#s", 1))
print(f("%-+5d|%+-5d|% 05d|%#.3x|%.0d|", 1, 2, 3, 4, 0))
"""),
    ("string-format/quoted", r"""
local f = string.format
print(f("%q", "line1\nline2\0tab\tquote\"back\\slash\r\1\127\200end"))
print(f("%q", 1), f("%q", -1), f("%q", math.mininteger), f("%q", math.maxinteger))
print(f("%q", 1.5), f("%q", 1/0), f("%q", -1/0), f("%q", 0/0), f("%q", 0.1), f("%q", 2^63), f("%q", -0.0))
print(f("%q", true), f("%q", false), f("%q", nil))
print(pcall(f, "%q", {}))
print(pcall(f, "%q", print))
print(f("%q", "\0001"), f("%q", "\r\n"), f("%q", "\226\130\172"))
print(load("return " .. f("%q", "round\0trip\n\"\\"))() == "round\0trip\n\"\\")
"""),
    ("patterns/find-match", r"""
print(("hello world"):find("o"), ("hello world"):find("o", 6), ("hello world"):find("o", -3), ("hello"):find("l+"))
print(("a.b"):find(".", 1, true), ("a.b"):find("%."), ("hello"):find(""), ("hello"):find("", 10), ("hello"):find("", 6))
print(("key=value"):match("(%w+)=(%w+)"), ("  trim  "):match("^%s*(.-)%s*$"), ("2024-01-15"):match("(%d+)-(%d+)-(%d+)"))
print(("hello"):match("()ll()"), ("THE (quick) fox"):find("%((%a+)%)"), ("abc"):match("^(a)"), ("abc"):match("^b"))
print(("f(a(b)c)d"):match("%b()"), ("THE (quick) fox"):match("%f[%a]%a+", 5), ("hello"):match(".-(l+)(.*)"))
print(("aaa"):match("a-b"), ("aaab"):match("a-b"), ("ab"):match("a?b"), ("b"):match("a?b"), ("abab"):match("(ab)%1"))
print(("x = 10, y = 20"):match("y = (%d+)"), ("%d"):match("%%d"), ("[test]"):match("%[(.*)%]"), ("a]b"):match("[]]"))
print(("hello123"):match("[%a]+"), ("hello123"):match("[^%a]+"), ("a-b"):match("[a%-]+"), ("abc"):match("[a-b]+"), ("\0x"):match("%z?x"))
for _, class in ipairs{"a", "c", "d", "g", "l", "p", "s", "u", "w", "x", "A", "D", "S", "W"} do
  local s = ""
  for b = 0, 127 do if string.char(b):find("%" .. class) then s = s .. b .. "," end end
  print(class, #s, s:sub(1, 60))
end
print(pcall(string.find, "a", "%"))
print(pcall(string.find, "a", "[a"))
print(pcall(string.find, "a", "(a"))
print(pcall(string.find, "a", "a)"))
print(pcall(string.find, "a", "%b"))
print(pcall(string.find, "a", "%f"))
print(pcall(string.match, "a", "(%1)"))
print(pcall(string.rep("(", 40) .. "a" .. string.rep(")", 40) and string.match, "a", string.rep("(", 40) .. "a" .. string.rep(")", 40)))
print(pcall(string.find, string.rep("a", 300000), string.rep("a?", 300000) .. string.rep("a", 300000)))
"""),
    ("patterns/gsub-gmatch", r"""
print(("hello world"):gsub("o", "0"), ("hello"):gsub("", "-"), ("abc"):gsub("%w", "%0%0"), ("abc"):gsub("(a)(b)", "%2%1"))
print(("hello world"):gsub("(%w+)", "<%1>", 1), ("$x and $y"):gsub("%$(%w+)", {x = "X", y = false}), pcall(string.gsub, "abc", ".", {a = 1, b = true}))
print(("1 2 3"):gsub("%d", function (d) return d * 2 end), ("abc"):gsub("b", function () return nil end), ("abc"):gsub("b", "%%"))
print(pcall(string.gsub, "abc", "(b)", "%2"))
print(pcall(string.gsub, "abc", "b", "%x"))
print(pcall(string.gsub, "abc", "b", function () return {} end))
print(pcall(string.gsub, "abc", "b", 1))
print(("abc"):gsub("b", 5), ("a.b.c"):gsub("%.", "/"), ("abc"):gsub("x*", "-"), ("hello"):gsub("l", "L", 0), ("hello"):gsub("l", "L", -1))
local words = {}
for w in ("one two  three"):gmatch("%a+") do words[#words + 1] = w end
print(table.concat(words, "|"))
for k, v in ("a=1, b=2"):gmatch("(%w+)=(%w+)") do io.write(k, v, ";") end print()
for p in ("abc"):gmatch("()") do io.write(p, " ") end print()
for m in ("aaa"):gmatch("^a") do io.write(m, " ") end print()
for m in ("hello world"):gmatch("%a+", 3) do io.write(m, " ") end print()
for m in ("abc"):gmatch("", -1) do io.write("[", m, "]") end print()
"""),
    ("string-pack/formats", r"""
local function hex(s) return (s:gsub(".", function (c) return string.format("%02x", c:byte()) end)) end
print(hex(string.pack("i1i2i4i8", 1, 2, 3, 4)), hex(string.pack(">i2<i2=i2", 1, 1, 1)), hex(string.pack("b B h H", -1, 255, -2, 65535)))
print(hex(string.pack("j J T", -1, 1, 2)), hex(string.pack("f d n", 1.5, -2.25, 1/3)), hex(string.pack("i3 I5 i16", -1, 2^33, -2)))
print(hex(string.pack("s1 s2 z", "ab", "cd", "ef")), hex(string.pack("c5", "ab")), hex(string.pack("!4 b i4", 1, 2)), hex(string.pack("b x i2 Xi4 b", 1, 2, 3)))
print(string.unpack("i1i2i4i8", string.pack("i1i2i4i8", -1, -2, -3, -4)))
print(string.unpack("z s1 c3", "hi\0\3abcxyz"), string.unpack("<I3", "\1\2\3"), string.unpack(">I3", "\1\2\3"))
print(string.unpack("i2", "\1\0\2\0", 3), string.unpack("i16", string.pack("i16", math.mininteger)), string.unpack("f", string.pack("f", 0.1)))
print(string.packsize("i1i2i4i8"), string.packsize("!8 b d"), string.packsize("c10 x"), string.packsize("<!4 i2 i8"), pcall(string.packsize, "!4 i3"))
print(pcall(string.pack, "i1", 200))
print(pcall(string.pack, "i17", 1))
print(pcall(string.pack, "c2", "abc"))
print(pcall(string.pack, "z", "a\0b"))
print(pcall(string.pack, "s1", string.rep("x", 300)))
print(pcall(string.unpack, "i4", "abc"))
print(pcall(string.unpack, "z", "abc"))
print(pcall(string.unpack, "i16", string.rep("\255", 15) .. "\127"))
print(pcall(string.packsize, "s"))
print(pcall(string.pack, "!3 i4", 1))
print(pcall(string.pack, "y", 1))
print(pcall(string.unpack, "b", "x", 3))
print(pcall(string.unpack, "b", "x", -5))
print(pcall(string.pack, "d", "x"))
print(pcall(string.pack, "Xz", 1))
"""),
    ("table-library/functions", r"""
local t = {1, 2, 3}
table.insert(t, 4); table.insert(t, 1, 0); table.insert(t, #t + 1, 5)
print(table.concat(t, ","), table.remove(t), table.remove(t, 1), table.concat(t, ","))
print(table.remove({}), table.remove({}, 0), #t, table.remove(t, #t + 1), select("#", table.remove({})))
print(pcall(table.insert, t, 10, 1))
print(pcall(table.insert, t, 0, 1))
print(pcall(table.insert, t, 1, 2, 3))
print(pcall(table.remove, t, 10))
print(table.concat({}, ","), table.concat({1, 2.5, "x"}, "-", 2), table.concat({1, 2, 3}, ", ", 2, 3), table.concat({1, 2}, "", 3))
print(pcall(table.concat, {1, {}, 3}))
print(pcall(table.concat, {1, 2}, ",", 1, 3))
print(table.unpack({1, 2, 3}, 2), table.unpack({1, 2, 3}, 2, 5), table.unpack({}, 1, 0), select("#", table.unpack({}, 1, 3)))
print(pcall(table.unpack, {}, 1, 1e8))
local p = table.pack(1, nil, 3)
print(p.n, p[1], p[2], p[3], table.pack().n)
local m = table.move({1, 2, 3, 4, 5}, 2, 4, 1)
print(table.concat(m, ","), table.concat(table.move({1, 2, 3}, 1, 3, 3), ","), table.concat(table.move({1, 2}, 1, 2, 1, {9, 9, 9}), ","))
print(pcall(table.move, {}, 1, math.maxinteger, 2))
local c = table.create(10, 5)
print(#c, next(c), pcall(table.create, -1))
print(pcall(table.create, 1 << 40))
local proxy = setmetatable({}, {__index = function (_, i) return i <= 3 and i * 10 or nil end, __len = function () return 3 end})
print(table.concat(proxy, "+"), table.unpack(proxy))
"""),
    ("table-library/sort", r"""
local t = {5, 2, 8, 1, 9, 3, 7, 4, 6, 0}
table.sort(t); print(table.concat(t, " "))
table.sort(t, function (a, b) return a > b end); print(table.concat(t, " "))
local words = {"banana", "Apple", "cherry", "apple", "Banana"}
table.sort(words); print(table.concat(words, " "))
local recs = {}
for i = 1, 30 do recs[i] = {key = i % 4, id = i} end
table.sort(recs, function (a, b) return a.key < b.key end)
local out = {}
for i, r in ipairs(recs) do out[i] = r.id end
print(table.concat(out, " "))
local calls = {}
local data = {3, 1, 2, 5, 4, 3, 1}
table.sort(data, function (a, b) calls[#calls + 1] = a .. "<" .. b; return a < b end)
print(table.concat(data, " "), #calls, table.concat(calls, " "))
print(pcall(table.sort, {1, "x", 2}))
print(pcall(table.sort, {3, 2, 1, 4, 5, 6}, function () return true end))
local mixed = {3.5, 1, -2, 2^53, -0.0, math.mininteger, 1e308}
table.sort(mixed); print(table.concat(mixed, " "))
print(pcall(table.sort, {1, 2}, 1))
"""),
    ("math-library/functions", r"""
print(math.abs(-3), math.abs(-3.5), math.abs(math.mininteger), math.ceil(3.2), math.ceil(-3.2), math.floor(3.7), math.floor(-3.7), math.floor(5))
print(math.fmod(7, 3), math.fmod(-7, 3), math.fmod(7, -3), math.fmod(7.5, 2), math.fmod(-6, 2), math.fmod(math.mininteger, -1), pcall(math.fmod, 1, 0))
print(math.fmod(1, 0.0), math.modf(3.7), math.modf(-3.7), math.modf(5), math.modf(1/0), math.modf(-1/0))
print(math.sqrt(16), math.sqrt(2), math.exp(0), math.exp(1), math.log(1), math.log(8, 2), math.log(100, 10), math.log(27, 3), math.log(2, 4))
print(math.sin(0), math.cos(0), math.tan(1), math.asin(1), math.acos(0), math.atan(1), math.atan(1, -1), math.atan(-0.0, -1), math.atan(0, 0))
print(math.max(1, 2.5, -1), math.min(1, 2.5, -1), math.max(3), math.max(1, 1.0), math.min(1.0, 1), pcall(math.max))
print(math.huge, -math.huge, math.pi, math.maxinteger, math.mininteger, math.ult(1, -1), math.ult(-1, 1), math.type(1//1), math.type(1/1), math.type(nil))
print(math.ceil(2^62 + 0.0), math.floor(2^63), math.ceil(-2^63), math.floor(1e100), math.ceil(-0.0), math.floor(-0.0))
print(math.tointeger(5.0), math.abs(-0.0), math.sqrt(-1) ~= math.sqrt(-1), math.log(0), math.log(-1) ~= math.log(-1), math.exp(1000))
print(string.format("%.17g %.17g %.17g %.17g", math.sin(1), math.cos(1), math.exp(2), math.log(10)))
print(pcall(math.floor, "a"))
print(pcall(math.ult, 1.5, 2))
print(pcall(math.abs))
"""),
    ("random/seeded", r"""
print(math.randomseed(42))
local t = {}
for i = 1, 8 do t[i] = math.random(1, 100) end
print(table.concat(t, " "))
print(math.random(), math.random(10), math.random(0), math.random(-5, -1), math.random(math.mininteger, math.maxinteger))
print(math.randomseed(1, 2))
print(math.random(3), math.random(1.0, 3.0), string.format("%.17g", math.random()))
print(pcall(math.randomseed, -1.5))
print(math.random(7))
print(pcall(math.random, 2, 1))
print(pcall(math.random, 1, 2, 3))
print(pcall(math.random, 1.5))
print(pcall(math.random, 0, math.maxinteger))
math.randomseed(0)
local counts = {0, 0, 0}
for i = 1, 3000 do local r = math.random(3); counts[r] = counts[r] + 1 end
print(counts[1], counts[2], counts[3])
"""),
    ("utf8/functions", r"""
print(utf8.char(72, 228, 8364, 128512, 0x7FFFFFFF):byte(1, -1))
print(utf8.char(), utf8.charpattern, utf8.len("häll€"), utf8.len(""), utf8.len("\xff"), utf8.len("abc\xe4"), utf8.len("häll€", 2), utf8.len("häll€", -3))
print(utf8.codepoint("häll€", 1, -1))
print(utf8.offset("häll€", 3), utf8.offset("häll€", -1), utf8.offset("häll€", 0, 3), utf8.offset("häll€", 10), utf8.offset("abc", 4))
for p, c in utf8.codes("aä€😀") do io.write(p, ":", c, " ") end print()
print(pcall(utf8.codepoint, "\xff"))
print(pcall(utf8.codepoint, "abc", 4))
print(pcall(utf8.char, -1))
print(pcall(utf8.char, 0x80000000))
print(pcall(utf8.offset, "häll€", 1, 3))
print(pcall(function () for p, c in utf8.codes("a\xffb") do end end))
print(utf8.len("\xed\xa0\x80"), utf8.len("\xed\xa0\x80", 1, -1, true), utf8.len("\xf4\x90\x80\x80"), utf8.len("\xf4\x90\x80\x80", 1, -1, true))
print(utf8.codepoint("\u{7FFFFFFF}", 1, 1, true), pcall(utf8.codepoint, "\u{7FFFFFFF}"))
print(utf8.len("\xc0\x80"), utf8.len("\xe0\x80\x80"), utf8.len(("x"):rep(10), 11), pcall(utf8.len, "x", 3))
for p, c in utf8.codes("\u{10FFFF}\u{D7FF}", true) do io.write(p, ":", c, " ") end print()
print(("häll€"):match(utf8.charpattern .. "$"), #utf8.char(0x10FFFF), utf8.offset("a\u{80}", 2), utf8.offset("€", -1, 4))
"""),
    ("coroutines/basics", r"""
local co = coroutine.create(function (a, b)
  print("start", a, b)
  local c = coroutine.yield(a + b)
  print("got", c)
  local d, e = coroutine.yield(c * 2)
  return d + e, "end"
end)
print(coroutine.status(co), coroutine.resume(co, 1, 2))
print(coroutine.status(co), coroutine.resume(co, 10))
print(coroutine.resume(co, 3, 4))
print(coroutine.status(co), coroutine.resume(co))
local gen = coroutine.wrap(function () for i = 1, 3 do coroutine.yield(i) end return "done" end)
print(gen(), gen(), gen(), gen(), pcall(gen))
print(coroutine.isyieldable(), select(2, coroutine.running()), type(coroutine.running()))
print(coroutine.resume(coroutine.create(function () return coroutine.isyieldable(), select(2, coroutine.running()) end)))
print(pcall(coroutine.yield, 1))
local err = coroutine.create(function () error("oops") end)
print(coroutine.resume(err))
print(coroutine.status(err), coroutine.close(err), coroutine.status(err))
local errt = coroutine.create(function () error({}) end)
print(coroutine.resume(errt) == false, type(select(2, coroutine.resume(errt))))
local wrapped = coroutine.wrap(function () error("wrapped") end)
print(pcall(wrapped))
local wrapped2 = coroutine.wrap(function () local x = nil; return x.y end)
print(pcall(wrapped2))
local nested = coroutine.wrap(function ()
  local inner = coroutine.wrap(function () coroutine.yield("inner") return "inner done" end)
  coroutine.yield(inner()); coroutine.yield(inner())
end)
print(nested(), nested())
print(pcall(coroutine.resume, nil))
print(coroutine.resume(coroutine.running()))
local self
self = coroutine.create(function () return coroutine.resume(self) end)
print(coroutine.resume(self))
print(coroutine.status(coroutine.create(print)), pcall(coroutine.status, 1))
"""),
    ("coroutines/close-yield", r"""
local co = coroutine.create(function ()
  local x <close> = setmetatable({}, {__close = function (_, e) print("closing", e) end})
  coroutine.yield(1)
end)
print(coroutine.resume(co))
print(coroutine.close(co), coroutine.status(co))
print(coroutine.close(coroutine.create(print)))
local co2 = coroutine.create(function ()
  local x <close> = setmetatable({}, {__close = function () error("close err") end})
  coroutine.yield()
end)
coroutine.resume(co2)
print(coroutine.close(co2))
print(pcall(coroutine.close, coroutine.running()))
local yp = coroutine.wrap(function ()
  local ok, v = pcall(function () local r = coroutine.yield("in pcall"); error(r) end)
  coroutine.yield(tostring(ok) .. " " .. v)
  return "after"
end)
print(yp(), yp("resumed error"), yp())
local mt = coroutine.wrap(function ()
  local t = setmetatable({}, {__index = function (_, k) return coroutine.yield(k) end})
  return t.key .. "!"
end)
print(mt(), mt("value"))
local sorter = coroutine.wrap(function ()
  table.sort({3, 2, 1}, function (a, b) coroutine.yield() return a < b end)
end)
print(pcall(sorter))
local iter = coroutine.wrap(function () for k, v in pairs({1}) do coroutine.yield(k, v) end end)
print(iter())
local deep = coroutine.wrap(function () local function f(n) if n == 0 then coroutine.yield("deep") else f(n - 1) end end f(100) return "ok" end)
print(deep(), deep())
"""),
    ("io-library/write-read", r"""
io.write("int ", 1, " float ", 1.5, " big ", 2^63, " neg ", -0.0, "\n")
print(io.write("chained"):write(" more\n") == io.stdout)
local f = assert(io.open("data.txt", "w"))
print(io.type(f), io.type(io.stdout), io.type(42))
f:write("line1\n", "line2\n", 3, " ", 4.5, "\n", "0x10 -7 1e2 .5 nan\n", "last")
print(f:seek("cur"), f:seek("set", 2), f:seek("end"))
f:close()
print(io.type(f), pcall(f.write, f, "x"))
print(tostring(f))
f = io.open("data.txt")
print(f:read("l"), f:read("L"), f:read("n", "n"), f:read("l"))
print(f:read("n", "n", "n", "n"), f:read("n"))
print(f:read("l"), f:read(1), f:read(0), f:read("a"), f:read("a"), f:read("l"), f:read(0))
f:close()
for l in io.lines("data.txt") do io.write("[", l, "]") end print()
for a, b in io.lines("data.txt", 2, "l") do io.write(a, "|", b or "nil", " ") end print()
for n in io.lines("nums.txt", "n") do io.write(n, ",") end print()
local g = io.open("data.txt")
for l in g:lines("L") do io.write(#l, " ") end print()
print(pcall(g.read, g))
g:close()
print(pcall(io.lines, "missing.txt"))
print(io.open("missing.txt"))
print(pcall(io.open, "data.txt", "rw"))
print(pcall(io.open, "data.txt", "q"))
local a = io.open("append.txt", "a"); a:write("one\n"); a:close()
a = io.open("append.txt", "a+"); a:write("two\n"); a:seek("set"); print(a:read("a")); a:close()
local rw = io.open("rw.txt", "w+"); rw:write("hello"); rw:seek("set", 1); print(rw:read(3)); rw:close()
print(io.open("."):read(1))
print(pcall(io.read, "x"))
print(io.stdout:setvbuf("no"), io.stdout:setvbuf("full", 1024), pcall(io.stdout.setvbuf, io.stdout, "bad"))
""", {"nums.txt": "1 2.5 0x1F -3 abc"}),
    ("io-library/stdin", r"""
print(io.read("n"), io.read("n"), io.read("l"), io.read("L"), io.read(3), io.read("a"), io.read("l"), io.read("a"))
""", [], "42 3.5e1 rest of line\nsecond\nthird line\nremaining\n"),
    ("io-library/stdin-lines", "for l in io.lines() do print(#l, l) end print(io.read())\n", [], "a\n\nbb\r\nlast"),
    ("io-library/redirect", r"""
local out = io.output("redirect.txt")
io.write("to file\n")
print("print still goes to stdout")
io.output():close()
print(pcall(io.write, "x"))
io.output(io.stdout)
io.input("redirect.txt")
print(io.read("a"))
io.input():close()
print(pcall(io.read))
io.input(io.stdin)
print(io.input() == io.stdin, io.output() == io.stdout, io.stderr:write("to stderr\n") == io.stderr)
print(pcall(io.output, "nodir/file.txt"))
print(pcall(io.close))
"""),
    ("io-library/popen", r"""
local p = io.popen("echo hello; echo world")
print(p:read("a"))
print(p:close())
print(io.popen("exit 3"):close())
print(io.popen("kill -s TERM $$"):close())
local w = io.popen("cat > piped.txt", "w")
w:write("through pipe\n")
print(w:close())
print(io.open("piped.txt"):read("a"))
print(pcall(io.popen, "true", "rw"))
print(os.execute("exit 5"))
print(os.execute("true"))
print(os.execute())
print(os.execute("kill -s INT $$"))
"""),
    ("os-library/time-date", r"""
print(os.time({year = 2020, month = 1, day = 1, hour = 0}), os.time({year = 2000, month = 1, day = 1}), os.time({year = 2020, month = 14, day = 35, hour = 25, min = 61, sec = 61}))
print(os.date("!%Y-%m-%d %H:%M:%S", 0), os.date("!%c", 1e9), os.date("!%x %X %p %A %a %B %b %j %U %W %w %y %Z %%", 1234567890))
print(os.date("%Y-%m-%d %H:%M:%S %z", 86400), os.date("!%D %e %F %g %G %h %I %n %R %r %t %T %u %V", 1700000000))
local t = os.date("*t", 1e9)
print(t.year, t.month, t.day, t.hour, t.min, t.sec, t.wday, t.yday, t.isdst)
local u = os.date("!*t", 0)
print(u.year, u.month, u.day, u.hour, u.wday, u.yday, u.isdst)
local n = {year = 2021, month = 2, day = 31}
print(os.time(n), n.month, n.day, n.yday, n.wday, n.hour, n.isdst)
print(os.difftime(10, 5), math.type(os.difftime(1, 1)), math.type(os.time({year = 2000, month = 1, day = 1})), pcall(os.difftime, 5))
print(pcall(os.date, "%Ez", 0))
print(pcall(os.date, "%", 0))
print(pcall(os.date, "%Q", 0))
print(pcall(os.time, {year = 2000}))
print(pcall(os.time, {year = 2000, month = "x", day = 1}))
print(pcall(os.time, {year = 2000, month = 1.5, day = 1}))
print(pcall(os.date, "%Y", 2^60))
print(os.date("!%Ec|%EC|%Ex|%EX|%Ey|%EY|%Od|%Oe|%OH|%OI|%Om|%OM|%OS|%Ou|%OU|%OV|%Ow|%OW|%Oy", 0))
print(os.date("", 0), #os.date("!" .. string.rep("%Y", 100), 0), type(os.clock()), type(os.time()), type(os.date()))
"""),
    ("os-library/environment-files", r"""
print(os.getenv("LUA_TEST_VALUE"), os.getenv("LUA_TEST_MISSING"), os.getenv("TZ"), os.getenv("LC_ALL"))
print(os.remove("victim.txt"), io.open("victim.txt"))
print(os.remove("victim.txt"))
print(os.rename("from.txt", "to.txt"), io.open("to.txt"):read("a"))
print(os.rename("nothing.txt", "x.txt"))
print(os.remove("dir"))
print(os.setlocale(), os.setlocale("C"), os.setlocale(nil, "numeric"), os.setlocale("xx_YY"), pcall(os.setlocale, "C", "bad"))
print(os.setlocale("", "all"))
print(type(os.tmpname()), os.exit == os.exit)
""", {"victim.txt": "v", "from.txt": "moved", "dir/inner.txt": "x"}),
]


COMPLETE = [
    ("debug-library/getinfo", r"""
local function sample(a, b, ...) local c = 1 return debug.getinfo(1, "nSlutfrL") end
local i = sample()
print(i.source, i.short_src, i.what, i.linedefined, i.lastlinedefined, i.currentline, i.nups, i.nparams, i.isvararg, i.name, i.namewhat, i.istailcall, i.func == sample)
local lines = {}
for l in pairs(i.activelines) do lines[#lines + 1] = l end
table.sort(lines); print(table.concat(lines, ","))
local p = debug.getinfo(print)
print(p.what, p.source, p.short_src, p.currentline, p.linedefined, p.nups, p.isvararg, p.nparams)
local m = debug.getinfo(1)
print(m.what, m.source, m.currentline, m.linedefined)
print(debug.getinfo(100), pcall(debug.getinfo, 1, "!"))
print(pcall(debug.getinfo, {}))
local function tail() return debug.getinfo(1, "t").istailcall end
local function caller() return tail() end
print(caller())
local t = {}
function t.fieldfn() return debug.getinfo(1, "n") end
local n = t.fieldfn()
print(n.name, n.namewhat)
local g = load("return debug.getinfo(1, 'S')", "=loaded")()
print(g.source, g.short_src, g.what)
local s = load("return debug.getinfo(1, 'S')", string.rep("long source ", 10))()
print(s.short_src)
local r = debug.getinfo(1, "r")
print(r.ftransfer, r.ntransfer)
"""),
    ("debug-library/locals-upvalues", r"""
local up1, up2 = 10, 20
local function f(a, b, ...)
  local x = "local"
  print(debug.getlocal(1, 1), debug.getlocal(1, 2), debug.getlocal(1, 3), debug.getlocal(1, 4), debug.getlocal(1, -1), debug.getlocal(1, -3))
  print(debug.setlocal(1, 3, "changed"), x, debug.setlocal(1, 50, 1))
  return up1 + up2
end
f(1, 2, "va1", "va2")
print(debug.getlocal(f, 1), debug.getlocal(f, 2), debug.getlocal(f, 3), debug.getlocal(print, 1))
print(debug.getupvalue(f, 1), debug.getupvalue(f, 2), debug.getupvalue(f, 3), debug.getupvalue(f, 0))
print(debug.setupvalue(f, 2, 100), up1, f(0, 0))
local function g() return up1 end
print(debug.upvalueid(f, 2) == debug.upvalueid(g, 1), debug.upvalueid(f, 3) == debug.upvalueid(g, 1), pcall(debug.upvalueid, f, 5))
local h1 = (function () local a = 1 return function () return a end end)()
local h2 = (function () local b = 2 return function () return b end end)()
debug.upvaluejoin(h1, 1, h2, 1)
print(h1(), debug.upvalueid(h1, 1) == debug.upvalueid(h2, 1), pcall(debug.upvaluejoin, h1, 2, h2, 1))
print(debug.getupvalue(string.gmatch("x", "x"), 1))
print(pcall(debug.getlocal, 50, 1))
local co = coroutine.create(function (p) local q = p * 2; coroutine.yield() end)
coroutine.resume(co, 21)
print(debug.getlocal(co, 1, 1), debug.getlocal(co, 1, 2), debug.getinfo(co, 1, "l").currentline)
print(debug.traceback(co))
print(debug.traceback(co, "msg", 1))
"""),
    ("debug-library/hooks-traceback", r"""
local lines = {}
local function hook(event, line) lines[#lines + 1] = event .. (line and (":" .. line) or "") end
local function work()
  local a = 1
  a = a + 1
  return a
end
debug.sethook(hook, "l")
work()
debug.sethook()
print(table.concat(lines, " "))
local calls = {}
debug.sethook(function (e) local i = debug.getinfo(2, "n") calls[#calls + 1] = e .. "/" .. tostring(i and i.name) end, "cr")
work()
debug.sethook()
print(table.concat(calls, " "))
local count = 0
debug.sethook(function () count = count + 1 end, "", 100)
for i = 1, 1000 do local _ = i * 2 end
debug.sethook()
print(count > 0, debug.gethook())
debug.sethook(print, "l", 5)
local hf, hm, hc = debug.gethook()
debug.sethook()
print(hf == print, hm, hc)
print(debug.traceback("message"))
print(debug.traceback("lvl", 2))
print(debug.traceback(123), debug.traceback(nil), type(debug.traceback({})))
local function lvl3() return debug.traceback("from lvl3", 1) end
local function lvl2() return lvl3() .. "" end
print(lvl2())
print(xpcall(function () local t = nil; return t.x end, debug.traceback))
"""),
    ("debug-library/metatables-registry", r"""
local mt = {__index = function (n, k) return n * k end, __len = function (x) return math.floor(x) end}
debug.setmetatable(10, mt)
print((5)[3], #2.7, getmetatable(1) == mt)
debug.setmetatable(10, nil)
print(getmetatable(1), pcall(function () return (5)[3] end))
debug.setmetatable(nil, {__index = function () return "nil index" end})
print((nil).x)
debug.setmetatable(nil, nil)
print(debug.setmetatable(print, {__index = {extra = "fn"}}) == print, print.extra)
debug.setmetatable(print, nil)
local locked = setmetatable({}, {__metatable = "locked"})
print(getmetatable(locked), type(debug.getmetatable(locked)))
print(type(debug.getregistry()), debug.getuservalue(1), debug.getuservalue(io.stdout, 1))
print(debug.setuservalue ~= nil, pcall(debug.setuservalue, {}, 1))
print(debug.setcstacklimit and debug.setcstacklimit(100))
"""),
    ("debug-library/interactive", r"""
print("before")
debug.debug()
print("after")
""", [], "print('inside debug')\nx = 5\nprint(x)\nerror('err in debug')\ncont\n"),
    ("binary-chunks/dump-load", r"""
local function hex(s) return (s:gsub(".", function (c) return string.format("%02x", c:byte()) end)) end
local function f(a, b) local c = a + b; return c * 2, "str", 1.5, nil, true end
local d = string.dump(f)
local s = string.dump(f, true)
print(#d, #s, hex(d:sub(1, 32)))
print(hex(s))
print(load(d)(1, 2))
print(load(s)(3, 4))
print(load(d, "bin", "b")(5, 6))
print(load(d, "bin", "t"))
print(load(d:sub(1, 20)))
print(load(d:sub(1, #d - 3)))
print(load("\27Lua\85\0garbage"))
print(load("\27Lua\84\0garbage"))
print(pcall(string.dump, print))
local up = 5
local g = load(string.dump(function () return up end))
print(type(select(2, pcall(g))))
print(hex(string.dump(load("return 42"))))
print(hex(string.dump(load("local x <const> = 2^53; return x, 'a\0b', -0.0, 1e300, math.mininteger"), true)))
local err = load(string.dump(load("error('dumped')", "@origin.lua")))
print(pcall(err))
local stripped = load(string.dump(load("\n\nerror('stripped')", "@origin.lua"), true))
print(pcall(stripped))
local fn = io.open("chunk.out", "wb"); fn:write(string.dump(load("return 'from file', ...")))
fn:close()
print(loadfile("chunk.out")("arg"), dofile("chunk.out"), loadfile("chunk.out", "t"))
"""),
    ("binary-chunks/cli", None, ["chunk.bin", "x"], "", {"chunk.bin": b"#comment\n\x1bLua"}),
    ("garbage-collector/control", r"""
print(collectgarbage("isrunning"), collectgarbage("stop"), collectgarbage("isrunning"), collectgarbage("restart"), collectgarbage("isrunning"))
print(collectgarbage(), collectgarbage("collect"), math.type(collectgarbage("count")), type(collectgarbage("step")), collectgarbage("step", 0) ~= nil)
print(collectgarbage("incremental"), collectgarbage("generational"), collectgarbage("incremental"), collectgarbage("incremental"))
for _, p in ipairs{"pause", "stepmul", "stepsize", "minormul", "majorminor", "minormajor"} do print(p, collectgarbage("param", p)) end
print(collectgarbage("param", "pause", 150), collectgarbage("param", "pause"), collectgarbage("param", "pause", 200))
print(pcall(collectgarbage, "param", "nonsense"))
print(pcall(collectgarbage, "nooption"))
print(pcall(collectgarbage, "setpause", 100))
print(pcall(collectgarbage, "count", "extra"))
"""),
    ("garbage-collector/finalizers", r"""
local order = {}
for i = 1, 5 do setmetatable({}, {__gc = function () order[#order + 1] = i end}) end
collectgarbage(); collectgarbage()
print(table.concat(order, " "))
local weak = setmetatable({}, {__mode = "k"})
local strong = {}
weak[strong] = 1; weak[{}] = 2; weak["str"] = 3; weak[1] = 4
collectgarbage()
local n = 0 for _ in pairs(weak) do n = n + 1 end
print(n, weak[strong], weak.str, weak[1])
local wv = setmetatable({}, {__mode = "v"})
wv[1] = {}; wv[2] = "string"; wv[3] = strong; wv[4] = 10
collectgarbage()
print(wv[1], wv[2], wv[3] == strong, wv[4])
local resurrected
setmetatable({name = "zombie"}, {__gc = function (o) resurrected = o end})
collectgarbage()
print(resurrected and resurrected.name)
local mt = {}
local late = setmetatable({}, mt)
mt.__gc = function () print("never: gc set after setmetatable") end
late = nil
collectgarbage()
setmetatable({}, {__gc = function () error("gc failure") end})
collectgarbage()
print("after failing gc")
local keep = setmetatable({}, {__gc = function () print("finalized at exit 1") end})
local keep2 = setmetatable({}, {__gc = function () print("finalized at exit 2") end})
print("end of script")
""", [], "", None, None, ["-W"]),
    ("garbage-collector/ephemeron", r"""
local e = setmetatable({}, {__mode = "k"})
do local k = {} e[k] = {ref = k} end
local alive = {}
e[alive] = {ref = alive}
collectgarbage()
local n = 0 for _ in pairs(e) do n = n + 1 end
print(n, e[alive].ref == alive)
local kv = setmetatable({}, {__mode = "kv"})
kv[{}] = 1; kv[1] = {}; kv.x = "y"
collectgarbage()
local c = 0 for _ in pairs(kv) do c = c + 1 end
print(c, kv.x)
"""),
    ("warnings/control", r"""
warn("not shown")
warn("@on")
warn("shown ", "in ", "pieces")
warn("@off")
warn("hidden")
warn("@on")
warn("@unknown control")
warn("@")
print(pcall(warn))
print(pcall(warn, "a", {}))
print(pcall(warn, 1))
warn("number ", "end")
"""),
    ("warnings/flag", "warn('with -W')\nwarn('@off')\nwarn('off now')\n", [], "", None, None, ["-W"]),
    ("lua-init/statement", None, ["-e", "print(X)"], "", None, {"LUA_INIT": "X = 'from init' print('init ran')"}),
    ("lua-init/versioned", None, ["-e", "print(X)"], "", None, {"LUA_INIT_5_5": "X = 'versioned'", "LUA_INIT": "X = 'plain'"}),
    ("lua-init/file", None, ["-e", "print(Y)"], "", {"init.lua": "Y = 'from file' print('file init', ...)"}, {"LUA_INIT": "@init.lua"}),
    ("lua-init/error", None, ["-e", "print('unreached')"], "", None, {"LUA_INIT": "error('init failed')"}),
    ("lua-init/missing-file", None, ["-e", "print('unreached')"], "", None, {"LUA_INIT": "@missing.lua"}),
    ("lua-init/ignored", None, ["-E", "-e", "print(X, package.path:find('custom') ~= nil)"], "", None, {"LUA_INIT": "X = 1", "LUA_PATH": "custom/?.lua"}),
    ("package/require", r"""
local m, path = require("mod")
print(m.name, path, require("mod") == m, package.loaded.mod == m)
print(require("sub.inner"))
package.preload.pre = function (...) return {args = table.pack(...)} end
local p, extra = require("pre")
print(p.args.n, p.args[1], p.args[2], extra)
print(pcall(require, "nope"))
print(pcall(require, "broken"))
print(pcall(require, "failing"))
print(package.searchpath("mod", "./?.lua;./?/init.lua"), package.searchpath("x.y", "?.z;?.w"))
print(package.searchpath("a.b", "?", "", "/"), package.searchpath("a.b", "?", ".", "_"))
print(package.config, #package.searchers, type(package.loadlib), type(package.searchers[1]))
print(package.path)
print(package.cpath)
print(require("string") == string, package.loaded._G == _G, package.loaded["_G"] ~= nil)
print(package.loadlib("missing_library.so", "f"))
package.path = 5
print(pcall(require, "zzz"))
""", [], "", {"mod.lua": "return {name = 'mod', args = {...}}", "sub/inner.lua": "return 'inner:' .. ...", "broken.lua": "return +", "failing.lua": "error('fails on load')"}),
    ("package/env-path", None, ["-e", "print(package.path) print(package.cpath) print(require('m'))"], "", {"lib/m.lua": "return 'found m'"}, {"LUA_PATH": "lib/?.lua;;", "LUA_CPATH": "c/?.so"}),
    ("package/versioned-path", None, ["-e", "print(package.path)"], "", None, {"LUA_PATH_5_5": "five/?.lua", "LUA_PATH": "plain/?.lua"}),
    ("cli-options/require-l", None, ["-l", "mod", "-l", "alias=mod", "-e", "print(mod.v, alias.v, mod == alias)"], "", {"mod.lua": "print('loading', ...) return {v = 1}"}),
    ("cli-options/require-l-missing", None, ["-l", "nothere"]),
    ("interactive/piped", None, ["-i"], "x = 1\nprint(x + 1)\n1 + 1\nreturn 2, 3\n'str'\nnil\nlocal y = 5\n=x\n"),
    ("interactive/incomplete", None, ["-i"], "for i = 1, 2 do\nprint(i)\nend\nfunction f()\nreturn 'f'\nend\nf()\n"),
    ("interactive/errors", None, ["-i"], "error('x')\nprint(1)\nx = = 1\nerror({})\nerror(setmetatable({}, {__tostring = function () return 'ts' end}))\nprint('alive')\nfor\n"),
    ("interactive/after-script", "x = 'from script'\n", ["arg1"], "print(x, arg[1])\n", None, None, ["-i"]),
    ("interactive/version-flag", None, ["-v", "-i"], "print('v')\n"),
    ("interactive/print-error", None, ["-e", "print = nil", "-i"], "10\n"),
    ("interactive/local-warning", None, ["-i", "-W"], "local z = 3\nz\n"),
    ("interactive/prompt", None, ["-e", "_PROMPT = 'P> ' _PROMPT2 = 'Q> '", "-i"], "if true then\nprint('x')\nend\n"),
    ("interactive/eof-continuation", None, ["-i"], "a.\n"),
    ("interactive/os-exit", None, ["-i"], "print('a')\nos.exit(4)\nprint('b')\n"),
    ("error-reporting/limits", r"""
local many = {}
for i = 1, 210 do many[i] = "local v" .. i end
print(load(table.concat(many, "\n"), "=limits"))
local ups = {"local f = function() return "}
for i = 1, 260 do table.insert(ups, 1, "local u" .. i .. " = " .. i .. "\n") end
local body = {}
for i = 1, 260 do body[i] = "u" .. i end
print(load(table.concat(ups) .. table.concat(body, "+") .. " end", "=limits"))
print(load(string.rep("a = {", 300) .. string.rep("}", 300), "=limits"))
print(pcall(load("return " .. string.rep("-", 300) .. "1", "=limits")))
print(load(string.rep("do ", 300) .. string.rep("end ", 300), "=limits"))
print(pcall(string.rep, "x", math.maxinteger))
local deep = setmetatable({}, {__index = function (t, k) return t[k + 1] end})
print(pcall(function () return deep[1] end))
print(pcall(function () local function r() return pcall(r) end return r() end))
print(pcall(table.concat, setmetatable({}, {__len = function () return 2^40 end})))
print(select("#", table.unpack({}, 1, 250)), pcall(table.unpack, {}, 1, 1e6))
"""),
]


SURFACE = [
    # Probes from the manual page lua.1 and the usage text.
    ("cli-options/manual-e", ["-e", "print(_VERSION)"]),
    ("cli-options/manual-i-script", ["-i", "main.lua"], "print('repl')\n"),
    ("cli-options/manual-l", ["-l", "main", "-e", "print(main)"]),
    ("cli-options/manual-l-global", ["-l", "g=main", "-e", "print(g)"]),
    ("cli-options/manual-v", ["-v"]),
    ("cli-options/manual-E", ["-E", "-e", "print(X)"], "", {"LUA_INIT": "X = 1"}),
    ("cli-options/manual-W", ["-W", "-e", "warn('manual')"]),
    ("cli-options/manual-double-dash", ["--", "main.lua", "-v"]),
    ("cli-options/manual-dash", ["-", "x"], "print(..., arg[0])\n"),
    ("cli-options/manual-no-args", [], "print('as lua -')\n"),
    ("cli-options/manual-args", ["main.lua", "a", "b"]),
    ("lua-init/manual-init-at", ["-e", "print('e')"], "", {"LUA_INIT": "@main.lua"}),
    ("lua-init/manual-init-5-5", ["-e", "print('e')"], "", {"LUA_INIT_5_5": "print('5.5')", "LUA_INIT": "print('plain')"}),
    ("package/manual-lua-path-5-5", ["-e", "print(package.path, package.cpath)"], "", {"LUA_PATH_5_5": "p55", "LUA_PATH": "p", "LUA_CPATH_5_5": "c55", "LUA_CPATH": "c"}),
    ("exit-status/manual-failure", ["-e", "error('x')"]),
    ("exit-status/manual-success", ["main.lua"]),
    ("interactive/manual-errors-no-exit", ["-i"], "error('no exit')\nprint('still running')\n"),
    ("cli-options/usage-e-arg", ["-e"]),
    ("cli-options/usage-option-after-script", ["main.lua", "-e", "print(1)"]),
    ("cli-options/usage-iv", ["-iv"]),
    ("cli-options/usage-Ex", ["-Ex", "--"]),
    ("cli-options/usage-empty-e", ["-e", "", "main.lua"]),
    ("cli-options/usage-e-joined", ["-eprint(7)"]),
    ("cli-options/usage-l-joined", ["-lmain", "-e", "print(main)"]),
]


def build(rows):
    result = []
    for row in rows:
        identity, source, *rest = row
        args = rest[0] if rest else []
        stdin = rest[1] if len(rest) > 1 else ""
        files = rest[2] if len(rest) > 2 and rest[2] else {}
        env = rest[3] if len(rest) > 3 else None
        pre = rest[4] if len(rest) > 4 else ()
        if source is None:
            result.append(probe(identity, args, stdin, files, env))
        elif isinstance(args, dict):
            result.append(script(identity, source, files=args))
        else:
            result.append(script(identity, source, *args, stdin=stdin, files=files, env=env, pre=pre))
    return result


def surface():
    main = "print('main', ...)\nreturn 'main module'\n"
    result = []
    for identity, args, *rest in SURFACE:
        stdin = rest[0] if rest else ""
        env = rest[1] if len(rest) > 1 else None
        result.append(probe(identity, args, stdin, {"main.lua": main}, env))
    return result


def milestones():
    return {"replay-core": build(CORE), "replay-extended": build(EXTENDED), "replay-complete": build(COMPLETE), "surface-manual": surface()}
