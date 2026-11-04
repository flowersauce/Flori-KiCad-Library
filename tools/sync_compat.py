"""Refresh generated legacy libraries and local legacy resource-path aliases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

from library_io import symbol_blocks


def safe_path(root: Path, relative: str) -> Path:
    """Reject manifest paths that escape the checkout."""
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path outside checkout: {relative}")
    return path


def load_layout(root: Path) -> dict:
    return json.loads((root / "tools/library-layout.json").read_text(encoding="utf-8"))


def legacy_libraries(root: Path, table_type: str) -> dict[str, str]:
    """Register both historical source names and their PCM-prefixed equivalents."""
    layout = load_layout(root)
    folder = "symbols" if table_type == "symbol" else "footprints"
    suffix = ".kicad_sym" if table_type == "symbol" else ".pretty"
    return {
        alias: f"${{FLORI_KICAD_DIR}}/compat/{folder}/{name}{suffix}"
        for name in layout[folder]
        for alias in (name, "PCM_" + name)
    }


def compatibility_outputs(root: Path, layout: dict) -> dict[Path, bytes]:
    """Construct legacy unions from the current canonical symbol/footprint files."""
    canonical_symbols = {}
    for path in sorted((root / "symbols").glob("Flori_*.kicad_sym")):
        canonical_symbols[path.stem] = symbol_blocks(path)
    outputs: dict[Path, bytes] = {}
    for nickname, members in layout["symbols"].items():
        header = canonical_symbols[next(iter(members.values()))][0]
        blocks = [canonical_symbols[library][1][name] for name, library in members.items()]
        text = header + "\n" + "".join("\t" + block + "\n" for block in blocks) + ")\n"
        outputs[safe_path(root, f"compat/symbols/{nickname}.kicad_sym")] = text.encode("utf-8")
    for nickname, members in layout["footprints"].items():
        for name, library in members.items():
            source = safe_path(root, f"footprints/{library}.pretty/{name}.kicad_mod")
            target = safe_path(root, f"compat/footprints/{nickname}.pretty/{name}.kicad_mod")
            outputs[target] = source.read_bytes()
    return outputs


def same_content(source: Path, target: Path) -> bool:
    if not target.is_file():
        return False
    if source.samefile(target):
        return True
    if source.stat().st_size != target.stat().st_size:
        return False
    return hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest()


def synchronize(root: Path, *, dry_run: bool = False) -> dict[str, int]:
    """Write changed legacy definitions and link their old resource paths locally."""
    root = root.resolve()
    layout = load_layout(root)
    outputs = compatibility_outputs(root, layout)
    changed_definitions = [path for path, data in outputs.items() if not path.exists() or path.read_bytes() != data]
    aliases = []
    for previous, current in layout["resource_aliases"].items():
        source = safe_path(root, current)
        if not source.is_file():
            raise FileNotFoundError(f"Legacy resource source is missing: {source}")
        target = safe_path(root, "compat/" + previous)
        if source == target:
            raise ValueError(f"Resource alias refers to itself: {previous}")
        if not same_content(source, target):
            aliases.append((source, target))
    if not dry_run:
        for path in changed_definitions:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".tmp")
            temporary.write_bytes(outputs[path])
            temporary.replace(path)
        for source, target in aliases:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            try:
                os.link(source, target)
            except OSError:
                shutil.copy2(source, target)
    return {"legacy_definitions": len(changed_definitions), "local_resource_aliases": len(aliases)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = synchronize(Path(__file__).resolve().parents[1], dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
