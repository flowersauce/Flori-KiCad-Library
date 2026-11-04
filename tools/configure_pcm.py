"""为已通过 PCM 安装的 Flori 包配置旧库别名和历史资源路径。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path

from library_io import merge_library_table


def configuration_directory(version: str) -> Path:
    """查找当前系统的 KiCad 版本配置目录。"""
    if override := os.environ.get("KICAD_CONFIG_HOME"):
        return Path(override).expanduser() / version
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Preferences"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "kicad" / version


def safe_path(root: Path, relative: str) -> Path:
    """限制清单中的路径只能位于指定根目录内。"""
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"清单路径越界：{relative}")
    return path


def same_content(source: Path, target: Path) -> bool:
    if not target.is_file():
        return False
    if source.samefile(target):
        return True
    if source.stat().st_size != target.stat().st_size:
        return False
    return hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="10.0", help="KiCad 配置版本，默认 10.0")
    parser.add_argument("--config-dir", type=Path, help="指定 KiCad 版本配置目录")
    parser.add_argument("--resources-dir", type=Path, default=Path(__file__).resolve().parent,
                        help="已安装包的 resources/<包标识> 目录")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入文件")
    args = parser.parse_args()
    resources = args.resources_dir.resolve()
    manifest_path = resources / "pcm-install.json"
    if not manifest_path.is_file():
        parser.error("未找到 pcm-install.json；请运行已安装包中的脚本，或传入 --resources-dir。")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    identifier = manifest["identifier"]
    if not re.fullmatch(r"[A-Za-z][-A-Za-z0-9.]{0,98}[A-Za-z0-9]", identifier):
        parser.error("安装清单中的包标识无效。")
    clean_identifier = identifier.replace(".", "_")
    if resources.name != clean_identifier or resources.parent.name != "resources":
        parser.error("资源目录应位于 PCM 的 resources/<包标识> 安装位置。")
    third_party = resources.parent.parent
    compatibility = safe_path(resources, "compat")
    external = os.environ.get("FLOWERSAUCE_KICAD_DIR")
    if external and Path(external).expanduser().resolve() != compatibility:
        parser.error("操作系统中的 FLOWERSAUCE_KICAD_DIR 覆盖了 KiCad 设置，请先调整该变量。")

    profile = args.config_dir or configuration_directory(args.version)
    config_path = profile / "kicad_common.json"
    try:
        original = config_path.read_bytes()
    except FileNotFoundError:
        parser.error(f"请先初始化 KiCad 配置：{config_path}")
    settings = json.loads(original.decode("utf-8-sig"))
    variables = settings.setdefault("environment", {}).setdefault("vars", {})
    changes: list[tuple[Path, bytes, bytes]] = []
    root_value = compatibility.as_posix()
    if variables.get("FLOWERSAUCE_KICAD_DIR") != root_value:
        variables["FLOWERSAUCE_KICAD_DIR"] = root_value
        newline = "\r\n" if b"\r\n" in original else "\n"
        updated = (json.dumps(settings, ensure_ascii=False, indent=4) + "\n").replace("\n", newline)
        changes.append((config_path, original, updated.encode("utf-8")))

    for filename, table_name, kind in (
        ("sym-lib-table", "sym_lib_table", "symbol"),
        ("fp-lib-table", "fp_lib_table", "footprint"),
    ):
        libraries = {}
        for nickname, installed_relative in manifest["legacy_libraries"][kind].items():
            target = safe_path(third_party, installed_relative)
            if not target.exists():
                parser.error(f"缺少已安装的兼容库：{target}")
            libraries[nickname] = "${KICAD10_3RD_PARTY}/" + installed_relative
        table_path = profile / filename
        try:
            before = table_path.read_bytes()
        except FileNotFoundError:
            parser.error(f"请先初始化 KiCad 标准库：{table_path}")
        try:
            after = merge_library_table(before, table_name, libraries)
        except ValueError as error:
            parser.error(f"{table_path}：{error}")
        if after != before:
            changes.append((table_path, before, after))

    aliases = []
    for previous, current in manifest["resource_aliases"].items():
        source = safe_path(third_party, current)
        target = safe_path(compatibility, previous)
        if not source.is_file():
            parser.error(f"缺少已安装的资源：{source}")
        if not same_content(source, target):
            aliases.append((source, target))
    print(f"PCM 包：{identifier} {manifest['version']}")
    print(f"旧资源根目录：{root_value}")
    print(f"待刷新资源链接：{len(aliases)}；待更新配置文件：{len(changes)}")
    for path, _, _ in changes:
        print(f"{'将更新' if args.dry_run else '更新'}：{path}")
    if args.dry_run:
        return
    for path, before, _ in changes:
        if path.read_bytes() != before:
            raise RuntimeError(f"配置在操作期间发生变化，请关闭 KiCad 后重试：{path}")
    for source, target in aliases:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()
        try:
            os.link(source, target)
        except OSError:
            shutil.copy2(source, target)
    suffix = uuid.uuid4().hex[:8]
    for path, _, data in changes:
        backup = path.with_name(f"{path.name}.flori-pcm-{suffix}.bak")
        temporary = path.with_name(f"{path.name}.flori-pcm-{suffix}.tmp")
        shutil.copy2(path, backup)
        temporary.write_bytes(data)
        temporary.replace(path)
        print(f"备份：{backup}")
    print("兼容配置已完成，可重新打开 KiCad。主库昵称由 PCM 管理。")


if __name__ == "__main__":
    main()
