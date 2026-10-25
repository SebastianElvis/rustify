#!/usr/bin/env python3
"""Install the local main-branch guard and preserve existing hooks."""

from pathlib import Path
import shlex
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def main():
    previous = Path(git("rev-parse", "--git-path", "hooks")).expanduser()
    previous = previous if previous.is_absolute() else ROOT / previous
    local = Path(git("rev-parse", "--git-path", "rustify-hooks"))
    local = local if local.is_absolute() else ROOT / local
    if previous.resolve() == local.resolve():
        print("The repository push guard is already active.")
        return
    local.mkdir(exist_ok=False)
    if previous.is_dir():
        for hook in previous.iterdir():
            if hook.is_file():
                (local / hook.name).symlink_to(hook.resolve())
    push = local / "pre-push"
    push.unlink(missing_ok=True)
    guard = shlex.quote(str(ROOT / ".githooks/pre-push"))
    old = previous / "pre-push"
    text = '#!/bin/sh\n'
    if old.is_file():
        text += 'input=$(mktemp) || exit 1\ntrap \'rm -f "$input"\' EXIT HUP INT TERM\ncat > "$input"\n'
        text += f'{guard} "$@" < "$input" || exit $?\n'
        text += f'{shlex.quote(str(old.resolve()))} "$@" < "$input"\n'
    else:
        text += f'exec {guard} "$@"\n'
    push.write_text(text)
    push.chmod(0o755)
    subprocess.run(["git", "-C", str(ROOT), "config", "--local", "core.hooksPath", str(local.resolve())], check=True)
    print("The repository push guard is active. Existing hooks remain connected.")


if __name__ == "__main__":
    main()
