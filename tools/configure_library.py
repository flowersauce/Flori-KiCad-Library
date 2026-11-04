"""Configure Flori source libraries, canonical PCM nicknames and legacy aliases."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from library_io import merge_library_table
from sync_compat import legacy_libraries, synchronize


VARIABLE = "FLORI_KICAD_DIR"
LEGACY_VARIABLE = "FLOWERSAUCE_KICAD_DIR"


def configuration_directory(version: str) -> Path:
    """Locate the versioned KiCad profile, respecting configuration overrides."""
    if override := os.environ.get("KICAD_CONFIG_HOME"):
        return Path(override).expanduser() / version
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Preferences"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "kicad" / version


def main() -> None:
    """Configure canonical resources and optionally merge library registrations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="10.0", help="KiCad profile version (default: 10.0)")
    parser.add_argument("--config-dir", type=Path, help="Override the versioned profile directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument(
        "--register-libraries", action="store_true",
        help="Merge canonical Flori libraries and historical aliases into the global tables",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    for directory in ("symbols", "footprints", "3dmodels", "resources/datasheets"):
        if not (repo_root / directory).is_dir():
            parser.error(f"This checkout is missing {directory}")
    roots = {VARIABLE: repo_root, LEGACY_VARIABLE: repo_root / "compat"}
    for name, root in roots.items():
        external = os.environ.get(name)
        if external and Path(external).expanduser().resolve() != root:
            parser.error(f"The operating-system variable {name} overrides this profile: {external}")

    profile = args.config_dir or configuration_directory(args.version)
    config_path = profile / "kicad_common.json"
    try:
        original = config_path.read_bytes()
    except FileNotFoundError:
        parser.error(f"KiCad profile not found: {config_path}. Open KiCad once, then close it.")
    settings = json.loads(original.decode("utf-8-sig"))
    variables = settings.setdefault("environment", {}).setdefault("vars", {})
    variable_changes = False
    print(f"Profile: {config_path}")
    for name, root in roots.items():
        value = root.as_posix()
        print(f"{name}={value}")
        if variables.get(name) != value:
            variables[name] = value
            variable_changes = True
    changes: list[tuple[Path, bytes, bytes]] = []
    if variable_changes:
        newline = "\r\n" if b"\r\n" in original else "\n"
        updated = (json.dumps(settings, ensure_ascii=False, indent=4) + "\n").replace("\n", newline)
        changes.append((config_path, original, updated.encode("utf-8")))

    if args.register_libraries:
        for filename, table_name, folder, pattern, kind in (
            ("sym-lib-table", "sym_lib_table", "symbols", "Flori_*.kicad_sym", "symbol"),
            ("fp-lib-table", "fp_lib_table", "footprints", "Flori_*.pretty", "footprint"),
        ):
            libraries = {}
            for path in sorted((repo_root / folder).glob(pattern)):
                if kind == "symbol" and not path.is_file():
                    continue
                if kind == "footprint" and not path.is_dir():
                    continue
                libraries["PCM_" + path.stem] = (
                    "${" + VARIABLE + "}/" + path.relative_to(repo_root).as_posix()
                )
            canonical_count = len(libraries)
            libraries.update(legacy_libraries(repo_root, kind))
            table_path = profile / filename
            try:
                table_original = table_path.read_bytes()
            except FileNotFoundError:
                parser.error(f"Initialize KiCad's standard libraries first: {table_path}")
            try:
                table_updated = merge_library_table(table_original, table_name, libraries)
            except ValueError as error:
                parser.error(f"{table_path}: {error}")
            if table_updated != table_original:
                changes.append((table_path, table_original, table_updated))
            print(
                f"Libraries: {canonical_count} canonical + "
                f"{len(libraries) - canonical_count} compatibility in {table_path}"
            )

    compatibility = synchronize(repo_root, dry_run=args.dry_run)
    print(f"Compatibility refresh: {json.dumps(compatibility)}")
    for path, _, _ in changes:
        print(f"{'Would update' if args.dry_run else 'Updating'}: {path}")
    if args.dry_run:
        return
    if not changes:
        print("Already configured.")
        return
    for path, before, _ in changes:
        if path.read_bytes() != before:
            raise RuntimeError(f"KiCad settings changed during setup: {path}. Close KiCad and run again.")
    identifier = uuid.uuid4().hex[:8]
    for path, _, data in changes:
        backup = path.with_name(f"{path.name}.flori-{identifier}.bak")
        temporary = path.with_name(f"{path.name}.flori-{identifier}.tmp")
        shutil.copy2(path, backup)
        temporary.write_bytes(data)
        temporary.replace(path)
        print(f"Backup: {backup}")
    print("Open KiCad to use Flori libraries.")


if __name__ == "__main__":
    main()
