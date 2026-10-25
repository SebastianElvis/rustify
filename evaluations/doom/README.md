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

- Source: doomgeneric commit `e257a09527062bfb986b6e5e0780839b6cbd5b71` and Freedoom 0.13.0. The SHA-256 values are in `reference.json`.
- Build: `scripts/build_reference.py doom` builds the SDL front end with the hardened profile and runs `strip`.
- The build removes the SDL_mixer music and sound objects. The reference binary has no sound.
- The binary links the Homebrew `sdl2-compat` library dynamically.

## Oracle

- Exact text output for startup and demo statistics.
- Exact frames at selected demo tics, with a capture method recorded as evidence.
- After the source reveal: the source audit maps the simulation and renderer components to the engine modules.

## Scope and limits

- The scope prioritizes startup, WAD loading, demo simulation, and the renderer.
- The scope excludes sound, music, networking, and multiplayer.
- `evaluations/doom/run.py` scores a project in `work/projects/doom` and writes reports to `work/evaluation/doom/`.
