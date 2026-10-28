"""Build a hardened reference binary from a pinned evaluation recipe."""

import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile

import yaml


ROOT = Path(__file__).resolve().parents[1]
CFLAGS = "-O3 -flto -fvisibility=hidden -DNDEBUG"
LDFLAGS = "-flto -Wl,-dead_strip"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, cwd, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{args} failed:\n{result.stderr[-4000:]}")
    return result.stdout


def fetch(source, downloads):
    path = downloads / source["name"]
    if not path.exists() or digest(path) != source["sha256"]:
        with urllib.request.urlopen(source["url"], timeout=120) as response:
            path.write_bytes(response.read())
    if digest(path) != source["sha256"]:
        raise ValueError("The source hash differs from the recipe: " + source["name"])
    return path


def extract(archive, destination):
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(destination)
    else:
        with tarfile.open(archive) as bundle:
            bundle.extractall(destination, filter="data")


def audit(binary, build_dir):
    """Record the metadata that remains visible to the reconstruction agent."""
    symbols = [line for line in run(["nm", "-U", str(binary)], ROOT).splitlines() if line.strip()]
    text = run(["strings", "-a", str(binary)], ROOT)
    sources = sorted(set(re.findall(r"[\w./-]+\.(?:c|cc|cpp|h)\b", text)))
    return {
        "defined_symbols": len(symbols),
        "source_file_strings": sources[:50],
        "source_file_string_count": len(sources),
        "build_path_leaks": text.count(str(build_dir)),
    }


def build(track):
    recipe = yaml.safe_load(next((ROOT / "eval").glob(f"*/{track}/reference.yaml"), ROOT / "eval" / track / "reference.yaml").read_text())
    work = ROOT / "work/references" / track
    downloads = ROOT / "work/downloads"
    build_dir = work / "build"
    shutil.rmtree(build_dir, ignore_errors=True)
    for directory in (downloads, build_dir):
        directory.mkdir(parents=True, exist_ok=True)
    for source in recipe["sources"]:
        archive = fetch(source, downloads)
        if source.get("extract", True):
            extract(archive, build_dir)
        else:
            shutil.copyfile(archive, build_dir / source["name"])
    env = dict(os.environ, CC="clang", CXX="clang++", CFLAGS=CFLAGS, CXXFLAGS=CFLAGS, LDFLAGS=LDFLAGS)
    logs = [run(["sh", "-c", step], build_dir / recipe["workdir"], env) for step in recipe["build"]]
    built = build_dir / recipe["workdir"] / recipe["binary"]
    binary = work / Path(recipe["binary"]).name
    shutil.copyfile(built, binary)
    run(["strip", str(binary)], ROOT)
    binary.chmod(0o755)
    resources = {name: digest(build_dir / path) for name, path in recipe.get("resources", {}).items()}
    for name, path in recipe.get("resources", {}).items():
        shutil.copyfile(build_dir / path, work / name)
    report = {
        "track": track,
        "binary": str(binary.relative_to(ROOT)),
        "binary_sha256": digest(binary),
        "resources": resources,
        "sources": recipe["sources"],
        "cflags": CFLAGS,
        "ldflags": LDFLAGS,
        "strip": "strip (all non-dynamic symbols)",
        "compiler": run(["clang", "--version"], ROOT).splitlines()[0],
        "platform": platform.platform(),
        "audit": audit(binary, build_dir),
    }
    (work / "build.yaml").write_text(yaml.safe_dump(report, sort_keys=False))
    (work / "build.log").write_text("\n".join(logs))
    shutil.rmtree(build_dir)
    return report
