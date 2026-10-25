"""Build the Doom cases: demos, options, savegames, recording, and error paths."""

import random
import struct

BASE = ["-iwad", "{iwad}", "-nogui"]
TIMEDEMO = ["-timedemo", "d.lmp", "-nodraw"]
SAVE, PAUSE = 0x82, 0x81  # BT_SPECIAL with BTS_SAVEGAME or BTS_PAUSE.
VERSIONS = ["1.666", "1.7", "1.8", "1.9", "hacx", "ultimate", "final", "final2", "chex"]


def demo(tics, skill=2, episode=1, level=1, players=1, deathmatch=0, respawn=0, fast=0, nomonsters=0, console=0, version=109, end=True):
    """Encode a demo lump. Each tic holds one command per player."""
    header = bytes([version, skill, episode, level, deathmatch, respawn, fast, nomonsters, console] + [int(i < players) for i in range(4)])
    long = version == 111
    body = b"".join(struct.pack("<bbHB" if long else "<bbBB", *command) for tic in tics for command in tic)
    return header + body + (b"\x80" if end else b"")


def command(rng):
    """Return a random forward, side, turn, and button command without special buttons."""
    buttons = rng.choice([0, 0, 0, 1, 1, 2, 3]) | (rng.random() < 0.05 and 4 | rng.randrange(8) << 3)
    return [rng.randint(-50, 50), rng.randint(-40, 40), rng.choice([0, 0, rng.randrange(256)]), buttons]


def walk(rng, length, players=1, long=False):
    """Hold each random command for a short run of tics, so that the players move through the map."""
    tics, held = [], [command(rng) for _ in range(players)]
    for _ in range(length):
        if rng.random() < 0.08:
            held = [command(rng) for _ in range(players)]
        tics.append([[f, s, (t << 8 if long else t), b] for f, s, t, b in held])
    return tics


def special(tics, marks, value=SAVE):
    """Set a special button on player 1 at each marked tic. Movement stays."""
    tics = [[list(cmd) for cmd in tic] for tic in tics]
    for slot, tic in enumerate(marks):
        tics[tic][0][3] = value | (slot % 8) << 2 if value == SAVE else value
    return tics


def still(length, players=1):
    return [[[0, 0, 0, 0]] * players for _ in range(length)]


def pwad(lumps):
    data, directory = b"", b""
    for name, value in lumps:
        directory += struct.pack("<ii8s", 12 + len(data), len(value), name.encode())
        data += value
    return b"PWAD" + struct.pack("<ii", len(lumps), 12 + len(data)) + data + directory


def case(identity, args, files=None, timeout=30, base=True):
    return {"id": identity, "steps": [{"args": (BASE if base else []) + args, "timeout": timeout}], "files": files or {}}


def timedemo(identity, lump, extra=(), files=None):
    return case(identity, [*extra, *TIMEDEMO], {"d.lmp": lump, **(files or {})})


def milestones():
    rng = random.Random(1993)
    short = demo(still(35))
    saves = demo(special(walk(rng, 700), range(87, 700, 88)))
    core = [
        timedemo("startup/default", short),
        timedemo("timedemo/still-35", short),
        timedemo("timedemo/walk-700", demo(walk(rng, 700))),
        timedemo("save-game/e1m1-every-88", saves),
        timedemo("save-game/all-slots", demo(special(walk(rng, 400), range(10, 400, 49)))),
        timedemo("simulation/e1m1-skill4", demo(special(walk(rng, 1500), range(186, 1500, 187)), skill=4)),
        case("iwad/missing", ["-iwad", "nosuch.wad", *TIMEDEMO], {"d.lmp": short}, base=False),
        case("iwad/not-a-wad", ["-iwad", "bad.wad", "-nogui"], {"bad.wad": b"not a wad file\n" * 4}, base=False),
        case("iwad/empty-directory", ["-iwad", "e.wad", "-nogui"], {"e.wad": b"IWAD" + struct.pack("<ii", 0, 12)}, base=False),
        case("iwad/none", ["-nogui", *TIMEDEMO], {"d.lmp": short}, base=False),
        case("demo-playback/missing-lump", ["-timedemo", "nosuch", "-nodraw"]),
        case("timedemo/builtin-name", ["-timedemo", "demo4", "-nodraw"]),
    ]
    extended = [timedemo(f"game-options/{'-'.join(a.lstrip('-') for a in args)}", short, args) for args in (
        ["-skill", "1"], ["-skill", "5"], ["-skill", "9"], ["-episode", "3"], ["-warp", "2", "5"], ["-warp", "4"],
        ["-deathmatch"], ["-altdeath"], ["-respawn"], ["-fast"], ["-nomonsters"], ["-turbo"], ["-turbo", "5"],
        ["-turbo", "999"], ["-timer", "3"], ["-avg"], ["-nosound", "-nosfx", "-nomusic"], ["-unknown-option", "x"])]
    extended += [timedemo(f"game-version/{name}", saves, ["-gameversion", name]) for name in VERSIONS + ["bogus"]]
    extended += [
        timedemo("devparm/flag", short, ["-devparm"]),
        timedemo("memory/mb-8", short, ["-mb", "8"]),
        timedemo("memory/mb-1", short, ["-mb", "1"]),
        timedemo("statdump/stdout", saves, ["-statdump", "-"]),
        timedemo("statdump/file", saves, ["-statdump", "stats.txt"]),
        timedemo("demo-format/longtics", demo(special(walk(rng, 300, long=True), [99, 199]), version=111)),
        timedemo("demo-format/version-110", demo(walk(rng, 100), version=110)),
        timedemo("demo-format/version-106-on-1.666", demo(special(walk(rng, 200), [150]), version=106), ["-gameversion", "1.666"]),
        timedemo("demo-format/longtics-flag", saves, ["-longtics"]),
        timedemo("demo-format/episode-4-map-9", demo(special(walk(rng, 300), [200]), episode=4, level=9, skill=3)),
        timedemo("demo-format/flags", demo(special(walk(rng, 400), [150, 350]), respawn=1, fast=1, skill=4)),
        timedemo("demo-format/nomonsters", demo(special(walk(rng, 300), [250]), nomonsters=1)),
        timedemo("netdemo/coop-2", demo(special(walk(rng, 500, 2), [100, 400]), players=2)),
        timedemo("netdemo/coop-4", demo(special(walk(rng, 500, 4), [100, 400]), players=4, level=2)),
        timedemo("netdemo/deathmatch-3", demo(special(walk(rng, 600, 3), [300, 599]), players=3, deathmatch=1, episode=2)),
        timedemo("netdemo/altdeath-2", demo(special(walk(rng, 600, 2), [300, 599]), players=2, deathmatch=2)),
        timedemo("netdemo/console-2", demo(special(walk(rng, 300, 2), [299]), players=2, console=1)),
        timedemo("netdemo/solo-net", saves, ["-solo-net"]),
        timedemo("netdemo/netdemo-flag", saves, ["-netdemo"]),
        timedemo("pause/toggle", demo(special(special(walk(rng, 500), [100, 300], PAUSE), [200, 400]))),
        timedemo("pause/held", demo(special(special(walk(rng, 300), [50], PAUSE), [299]))),
        case("pwad/demo-lump", ["-file", "p.wad", "-timedemo", "short", "-nodraw"], {"p.wad": pwad([("SHORT", saves)])}),
        case("pwad/missing", ["-file", "nosuch.wad", *TIMEDEMO], {"d.lmp": short}),
        case("response-file/args", ["@args.rsp"], {"args.rsp": b"-iwad {iwad}\n-nogui -skill 3\n-timedemo d.lmp -nodraw\n", "d.lmp": short}, base=False),
        case("response-file/missing", ["@nosuch.rsp", *BASE, *TIMEDEMO], {"d.lmp": short}, base=False),
    ]
    complete = [
        case("demo-playback/end", ["-playdemo", "d.lmp"], {"d.lmp": demo(special(walk(rng, 70), [60]))}, timeout=40),
        case("demo-playback/pwad-end", ["-file", "p.wad", "-playdemo", "short"], {"p.wad": pwad([("SHORT", demo(still(40)))])}, timeout=40),
        case("demo-recording/maxdemo", ["-record", "r", "-maxdemo", "1", "-skill", "4", "-warp", "1", "3"], timeout=40),
        case("demo-recording/longtics", ["-record", "r", "-maxdemo", "1", "-longtics", "-respawn", "-fast"], timeout=40),
        timedemo("demo-recording/during-timedemo", short, ["-record", "r"]),
        timedemo("configuration/paths", short, ["-config", "my.cfg", "-extraconfig", "extra.cfg"], {"my.cfg": b"screenblocks 11\n"}),
        {"id": "load-game/roundtrip", "files": {"d.lmp": demo(special(walk(rng, 300), [250]), skill=3, level=4)}, "steps": [
            {"args": BASE + TIMEDEMO, "timeout": 30},
            {"args": BASE + ["-loadgame", "0", "-record", "r", "-maxdemo", "1"], "timeout": 40}]},
        case("load-game/wrong-version", ["-loadgame", "1", "-record", "r", "-maxdemo", "1"], {".savegame/doomsav1.dsg": bytes(24) + b"version 108".ljust(16, b"\0") + bytes(20)}, timeout=40),
    ]
    return {"replay-core": core, "replay-extended": extended, "replay-complete": complete}


OPTIONS = [["-skill", "{1-5}"], ["-episode", "{1-4}"], ["-warp", "{1-4}", "{1-9}"], ["-deathmatch"], ["-altdeath"], ["-respawn"], ["-fast"],
           ["-nomonsters"], ["-turbo", "{10-400}"], ["-timer", "{1-30}"], ["-avg"], ["-devparm"], ["-gameversion", VERSIONS], ["-mb", "{6-32}"],
           ["-statdump", "-"], ["-longtics"], ["-solo-net"], ["-netdemo"], ["-config", "c.cfg"], ["-extraconfig", "x.cfg"], ["-nosound"]]


def generate(seed=1993, count=60):
    """Draw seeded demos and option sets that cover every demo field and every terminating option."""
    rng, cases = random.Random(seed), []
    for index in range(count):
        args = []
        for option in rng.sample(OPTIONS, rng.randint(0, 5)):
            for part in option:
                if isinstance(part, list):
                    part = rng.choice(part)
                elif part.startswith("{"):
                    low, high = map(int, part[1:-1].split("-"))
                    part = str(rng.randint(low, high))
                args.append(part)
        players, long = rng.choice([1, 1, 1, 2, 3, 4]), rng.random() < 0.15
        length = rng.randint(50, 1200)
        tics = special(walk(rng, length, players, long), sorted(rng.sample(range(length), rng.randint(1, 6))))
        lump = demo(tics, rng.randrange(5), rng.randint(1, 4), rng.randint(1, 9), players, rng.choice([0, 0, 1, 2]) if players > 1 else 0,
                    int(rng.random() < 0.2), int(rng.random() < 0.2), int(rng.random() < 0.1), 0, 111 if long else 109)
        cases.append(timedemo(f"simulation/generated-{index:03d}", lump, args))
    return cases


def upstream(wad):
    """Replay each built-in Freedoom demo plainly and with eight evenly spaced savegames."""
    reports = {}
    for name in ("DEMO1", "DEMO2", "DEMO3", "DEMO4"):
        lump, _ = wad.lump(name)
        players = sum(lump[9:13])
        size = 4 * players
        body = bytearray(lump[13:-1])
        tics = len(body) // size
        for slot in range(8):
            body[(slot + 1) * tics // 9 * size + 3] = SAVE | slot << 2
        reports[f"upstream-{name.lower()}"] = [
            case(f"timedemo/{name.lower()}", ["-timedemo", name.lower(), "-nodraw"]),
            timedemo(f"save-game/{name.lower()}-eight-saves", lump[:13] + bytes(body) + b"\x80"),
        ]
    return reports
