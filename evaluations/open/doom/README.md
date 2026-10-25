# Doom track

## Product

Doom is the 1993 first-person shooter from id Software.
id Software released the engine source in 1997.
The engine has many ports.
This track uses doomgeneric, a portable Doom engine based on Chocolate Doom, with its SDL2 front end.
The game data is Freedoom: Phase 1, a free replacement for the original game data.

## Selection rationale

- The track adds a real-time game to the dataset.
- The agent must recover a WAD data loader, a fixed-point game simulation, a BSP software renderer, menus, and a status bar.
- Doom demos replay recorded input. The simulation is deterministic, so demo playback gives an exact oracle for game logic and frames.
- The track tests the `game` profile and GUI capture. The other GUI track, zenity, uses only dialogs.
- Doom is famous and well studied. The track also tests how the agent separates binary evidence from prior knowledge.

## Reference build

- Source: doomgeneric commit `e257a09527062bfb986b6e5e0780839b6cbd5b71` and Freedoom 0.13.0. The SHA-256 values are in `reference.yaml`.
- Build: `scripts/build_reference.py doom` builds the SDL front end with the hardened profile and runs `strip`.
- The build removes the SDL_mixer music and sound objects. The reference binary has no sound.
- The binary links the Homebrew `sdl2-compat` library dynamically.

## Oracle

- Exact text output for startup and demo statistics.
- Exact frames at selected demo tics, with a capture method recorded as evidence.
- After the source reveal: the source audit maps the simulation and renderer components to the engine modules.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers the complete game: startup, menus, game play, demos, the renderer, the HUD and status bar, save games, configuration, and networking.
- The reference build has no sound because it omits the SDL_mixer objects. The reconstruction matches that binary.
- `run.py` scores a project in `work/projects/doom` and writes reports to `work/evaluation/doom/`.

## Scorer

`run.py` drives the binary through `runner.py`.
Each case runs in a new temporary directory with `LC_ALL=C`, `TZ=UTC`, and a temporary `HOME`.
Each case passes `-iwad` with the pinned `freedoom1.wad` and `-nogui`, so that `I_Error` opens no dialog.
The runner compares stdout, stderr, exit status, and the files in the working directory after each step.

- `-timedemo <demo> -nodraw` runs one tic per loop and ends with `I_Error("timed %i gametics ...")`. Most cases use it.
- A demo tic with `BT_SPECIAL | BTS_SAVEGAME` makes the engine write `.savegame/doomsavN.dsg`. The savegame is the oracle for the simulation state at that tic.
- A demo tic with `BT_SPECIAL | BTS_PAUSE` toggles the pause.
- `-record <name> -maxdemo 1` in live play ends after a full demo buffer with `Demo <name>.lmp recorded`.

| Report | Distinguisher | Content |
| --- | --- | --- |
| `repeatability` | Control | The reference against itself on every case. |
| `replay-core` | D-replay | Startup, IWAD loading and errors, demo replay, savegames. |
| `replay-extended` | D-replay | Every terminating option, game versions, demo formats, net demos, pause, PWAD, response files. |
| `replay-complete` | D-replay | `-playdemo` end, demo recording, save and load round trip, configuration paths. It also lists the manual items. |
| `generate-demos` | D-generate | 60 seeded demos (seed 1993) with random headers, players, long tics, savegames, and option sets. |
| `upstream-demo1` to `upstream-demo4` | D-upstream | The built-in Freedoom demos, plain and with eight savegames. doomgeneric has no test suite. |

The build compiles out `LoadResponseFile`, `LoadDefaultCollection`, and `StatDump` (`ORIGCODE` is undefined). The cases check that `@file`, configuration files, and `-statdump` change only the startup text.

The scorer also runs two negative controls: a script with wrong output and a wrapper that adds `-gameversion final`. Both must fail.

## Variable fields

The runner applies only these rules. Each rule has evidence in the source and in repeated reference runs.

- `zone memory: 0x...` on stdout: `Z_Init` prints the address that `malloc` returns. The address changes on every run because of ASLR. The runner keeps the line and masks the hex digits.
- `in N realtics (F fps)` on stderr: `G_CheckDemoStatus` measures wall time. The runner masks `N` and `F`. The gametic count stays exact.
- Pointer fields in `.dsg` files: `p_saveg.c` writes raw pointers with `saveg_writep` (thinker links, `snext`, `bnext`, `subsector`, `info`, `target`, `tracer`, player `mo`, `message`, `attacker`, and special thinker links). The values change with ASLR. The runner replaces each pointer with `1` if it is not null, or `0` if it is null. All other bytes stay exact.
- `count` of a moving platform in `.dsg` files: `EV_DoPlat` allocates `plat_t` with `Z_Malloc` and sets `count` only for some types. `T_PlatRaise` reads `count` only in the `waiting` state. Two reference runs give different bytes there. The runner sets `count` to `0` when the status is not `waiting` and the platform does not wait in stasis.
- Recursive `W_GetNumForName` errors after `-playdemo`: at the end of a demo, `G_CheckDemoStatus` fails on the demo lump name, calls `I_Error`, and `I_Error` calls `G_CheckDemoStatus` again as an exit function. The recursion ends in a stack overflow (`SIGSEGV`). The repeat count depends on the native stack frame size. The runner keeps the first error block and replaces the repeats with one marker. The exit signal and the empty stdout stay exact.

## Manual coverage

The scorer cannot measure frames on this host.
The SDL front end draws frames only to the window.
The in-engine screenshot (`V_ScreenShot`) needs a key event, `key_menu_screenshot` is unbound by default, and `LoadDefaultCollection` is compiled out, so no configuration can bind it.
Synthetic key events and screen capture need macOS Accessibility and Screen Recording permissions, which the scorer does not have.
Frame parity, menus, the status bar, the HUD, the automap, cheats, keyboard play, and the window state therefore stay in scope as manual items.
`replay-complete` lists them in its `manual` field.
With these permissions, a demo can pause with `BTS_PAUSE` and the operator can capture the static window. The status bar face still changes during the pause, because `ST_Ticker` runs.
