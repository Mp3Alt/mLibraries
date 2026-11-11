"""Build a source distribution from the checked-in mLibraries source map."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative: str) -> bytes:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f"Missing or out-of-project file: {relative}")
    return path.read_bytes()


def main() -> None:
    manifest = json.loads(read_project_file("mLibraries.json"))
    version = manifest["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", version):
        raise ValueError("Invalid distribution version")

    files = {
        "README.md": read_project_file("docs/distribution-readme.md"),
        "LICENSE": read_project_file("LICENSE"),
        "mLibraries.json": read_project_file("mLibraries.json"),
        "docs/testing.md": read_project_file("docs/testing.md"),
    }
    paths = set()
    for item in manifest["modules"] + manifest["tests"]:
        if item["path"] in paths:
            raise ValueError(f"Duplicate asset path: {item['path']}")
        paths.add(item["path"])
        if not item["path"].split("/")[-1].startswith("m"):
            raise ValueError(f"Module is missing the m prefix: {item['path']}")
        if item["type"] not in {"module", "server", "client"}:
            raise ValueError(f"Invalid script type: {item['type']}")
        files[item["source"]] = read_project_file(item["source"])

    for item in manifest["modules"]:
        relative = f"docs/api/{item['name']}.md"
        files[relative] = read_project_file(relative)
    for path in sorted((ROOT / "docs/verification").glob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        files[relative] = read_project_file(relative)
    for name in ["2026-11-11-sources.json", "2026-11-11-summary.json"]:
        relative = f"docs/verification/{name}"
        files[relative] = read_project_file(relative)

    hashes = {
        "name": manifest["name"],
        "version": version,
        "files": {
            name: {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
            for name, content in sorted(files.items())
        },
    }
    files["source-manifest.json"] = (json.dumps(hashes, indent=2) + "\n").encode("utf-8")

    destination = ROOT / "dist" / f"mLibraries-{version}.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            # Fixed metadata makes repeated builds from the same bytes identical.
            entry = zipfile.ZipInfo(f"mLibraries-{version}/{name}", date_time=(2026, 11, 11, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, content)

    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("Distribution integrity check failed")
        for name, content in files.items():
            if archive.read(f"mLibraries-{version}/{name}") != content:
                raise ValueError(f"Distribution content mismatch: {name}")
    print(json.dumps({"archive": str(destination), "files": len(files), "bytes": destination.stat().st_size}))


if __name__ == "__main__":
    main()
