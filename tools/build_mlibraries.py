"""Build a source ZIP from the library source map."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXTRA_FILES = [
    "tools/performance/analyze-library.py", "tools/performance/analyze-remote.py",
    "docs/testing.md", "docs/roadmap.md", "docs/ui-libraries.md",
    "docs/architecture/ui-libraries.md", "docs/community/mLibraries-devboard-topic.md",
    "docs/mPacket.md", "docs/mTopbar.md", "docs/mNet.md", "docs/mState.md",
    "docs/mPlayer.md", "docs/mData.md", "docs/mStore.md", "docs/mBan.md",
    "docs/mMessaging.md", "docs/mSpring.md",
    "docs/verification/2026-11-11.md",
    "docs/verification/2026-11-11-sources.json",
    "docs/verification/2026-11-11-summary.json",
    "docs/verification/libraries-0.12.2.md",
    "docs/verification/libraries-0.12.2.json",
]

def read_file(relative: str) -> bytes:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f"Missing or out-of-project file: {relative}")
    return path.read_bytes()

def collect_files() -> tuple[dict, dict[str, bytes]]:
    manifest = json.loads(read_file("mLibraries.json"))
    version = manifest["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", version):
        raise ValueError("Invalid distribution version")
    files = {
        "README.md": read_file("docs/distribution-readme.md"),
        "LICENSE": read_file("LICENSE"),
        "CHANGELOG.md": read_file("CHANGELOG.md"),
        "mLibraries.json": read_file("mLibraries.json"),
        "tools/build_mlibraries.py": read_file("tools/build_mlibraries.py"),
    }
    for name in EXTRA_FILES:
        files[name] = read_file(name)
    paths = set()
    for section in ["modules", "runtime", "tests", "examples"]:
        for entry in manifest.get(section, []):
            if entry["path"] in paths:
                raise ValueError(f"Duplicate asset path: {entry['path']}")
            paths.add(entry["path"])
            if not entry["path"].split("/")[-1].startswith("m"):
                raise ValueError(f"Asset is missing the m prefix: {entry['path']}")
            if entry["type"] not in {"module", "server", "client"}:
                raise ValueError(f"Invalid script type: {entry['type']}")
            files[entry["source"]] = read_file(entry["source"])
    for entry in manifest["modules"]:
        name = f"docs/api/{entry['name']}.md"
        files[name] = read_file(name)
    return manifest, files

def build(output: Path | None = None) -> Path:
    manifest, files = collect_files()
    prefix = f"mLibraries-{manifest['version']}"
    hashes = {
        "name": manifest["name"], "version": manifest["version"],
        "files": {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                  for name, data in sorted(files.items())},
    }
    files["source-manifest.json"] = (json.dumps(hashes, indent=2) + "\n").encode()
    destination = output or ROOT / "dist" / (prefix + ".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(prefix + "/" + name, date_time=(2026, 11, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        for name, data in files.items():
            if archive.read(prefix + "/" + name) != data:
                raise ValueError(f"ZIP content mismatch: {name}")
    print(json.dumps({"archive": str(destination), "files": len(files), "bytes": destination.stat().st_size}))
    return destination

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write the ZIP to this path.")
    args = parser.parse_args()
    build(args.output)
