"""从可编辑源码生成独立的 PCM 安装包及仓库索引，不修改源码或 KiCad 配置。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from sync_compat import compatibility_outputs, load_layout


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def installed_path(relative: str, identifier: str) -> str:
    category, rest = relative.split("/", 1)
    return f"{category}/{identifier}/{rest}"


def package_payload(root: Path, identifier: str, version: str) -> dict[str, bytes]:
    """只收集明确的库与资源类型；兼容定义直接从当前主库生成。"""
    layout = load_layout(root)
    clean_identifier = identifier.replace(".", "_")
    payload: dict[str, bytes] = {}
    patterns = (
        "symbols/Flori_*.kicad_sym",
        "footprints/Flori_*.pretty/*.kicad_mod",
        "3dmodels/Flori_*.3dshapes/*",
        "resources/datasheets/**/*",
        "resources/drawings/**/*",
    )
    allowed = {".kicad_sym", ".kicad_mod", ".step", ".stp", ".wrl", ".pdf", ".dwg"}
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path.suffix.lower() in allowed:
                if not path.resolve().is_relative_to(root):
                    raise ValueError(f"资源链接指向仓库外：{path}")
                payload[path.relative_to(root).as_posix()] = path.read_bytes()
    for path, data in compatibility_outputs(root, layout).items():
        payload[path.relative_to(root / "compat").as_posix()] = data
    if not any(name.startswith("symbols/Flori_") for name in payload):
        raise ValueError("未找到主符号库")
    for name, data in list(payload.items()):
        if not name.endswith((".kicad_sym", ".kicad_mod")):
            continue
        text = data.decode("utf-8-sig")
        for category in ("3dmodels", "resources"):
            text = text.replace(
                f"${{FLORI_KICAD_DIR}}/{category}/",
                f"${{KICAD10_3RD_PARTY}}/{category}/{clean_identifier}/",
            )
        if "${FLORI_KICAD_DIR}" in text or "${FLOWERSAUCE_KICAD_DIR}" in text:
            raise ValueError(f"存在未转换的源码路径：{name}")
        # 官方路径变量与 Reference 等器件字段保持原样。
        for category, target in re.findall(
            r'\$\{KICAD10_3RD_PARTY\}/(3dmodels|resources)/' + re.escape(clean_identifier) + r'/([^"\r\n]+)', text
        ):
            if f"{category}/{target}" not in payload:
                raise ValueError(f"{name} 引用了包内缺失资源：{target}")
        for library, footprint in re.findall(
            r'\(property\s+"Footprint"\s+"PCM_(Flori_[^:"]+):([^"\r\n]+)"', text
        ):
            if f"footprints/{library}.pretty/{footprint}.kicad_mod" not in payload:
                raise ValueError(f"{name} 引用了包内缺失封装：{library}:{footprint}")
        payload[name] = text.encode("utf-8")

    legacy = {}
    for kind, folder, suffix in (
        ("symbol", "symbols", ".kicad_sym"),
        ("footprint", "footprints", ".pretty"),
    ):
        legacy[kind] = {
            alias: installed_path(f"{folder}/{nickname}{suffix}", clean_identifier)
            for nickname in layout[folder]
            for alias in (nickname, "PCM_" + nickname)
        }
    resource_aliases = {}
    for previous, current in layout["resource_aliases"].items():
        if current not in payload:
            raise ValueError(f"兼容资源不在包中：{current}")
        resource_aliases[previous] = installed_path(current, clean_identifier)
    payload["resources/pcm-install.json"] = json_bytes({
        "identifier": identifier,
        "version": version,
        "legacy_libraries": legacy,
        "resource_aliases": resource_aliases,
    })
    for source, target in (
        ("tools/configure_pcm.py", "resources/configure_pcm.py"),
        ("tools/library_io.py", "resources/library_io.py"),
        ("pcm/INSTALL_zh.md", "resources/INSTALL_zh.md"),
        ("pcm/LICENSES_zh.md", "resources/licenses/README.md"),
        ("LICENSE", "resources/licenses/LICENSE"),
        ("LICENSES/KiCad-Libraries-LICENSE.md", "resources/licenses/KiCad-Libraries-LICENSE.md"),
    ):
        payload[target] = (root / source).read_bytes()
    for source, target in (
        ("imported-stock-assets-2026-11-04.json", "imported-stock-assets.json"),
        ("flori-migration-2026-11-04.json", "flori-migration.json"),
    ):
        record = json.loads((root / "docs/audits" / source).read_text(encoding="utf-8"))
        record.pop("backup", None)
        payload[f"resources/provenance/{target}"] = json_bytes(record)
    return payload


def version_key(version: dict) -> tuple[int, ...]:
    parts = tuple(int(part) for part in version["version"].split("."))
    return parts + (0,) * (3 - len(parts))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="自动日历版本，例如 2026.1104.123")
    parser.add_argument("--status", choices=("stable", "testing", "development"), default="testing")
    parser.add_argument("--repository", help="GitHub owner/repository，默认读取元数据主页")
    parser.add_argument("--source-commit", help="源码提交完整 SHA，附在发布说明中")
    parser.add_argument("--output-dir", type=Path, default=Path("dist/pcm"))
    parser.add_argument("--previous-packages", type=Path, help="上一版 packages.json，用于保留版本历史")
    parser.add_argument("--previous-packages-url", help="上一版公开索引 URL；仅 404 视为首次发布")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,6}", args.version):
        parser.error("版本必须为三段数字，位数上限为 4、4、6")
    if args.source_commit and not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", args.source_commit):
        parser.error("--source-commit 必须为完整的小写十六进制提交 SHA")
    if args.previous_packages and args.previous_packages_url:
        parser.error("上一版索引只能选择文件或 URL 之一")
    root = Path(__file__).resolve().parents[1]
    metadata = json.loads((root / "pcm/metadata.json").read_text(encoding="utf-8"))
    identifier = metadata["identifier"]
    if not re.fullmatch(r"[A-Za-z][-A-Za-z0-9.]{0,98}[A-Za-z0-9]", identifier):
        parser.error("PCM 包标识不合法")
    repository = args.repository or metadata["resources"]["homepage"].removeprefix("https://github.com/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        parser.error("--repository 必须为 GitHub owner/repository")
    metadata["resources"]["homepage"] = f"https://github.com/{repository}"
    version = {key: value for key, value in metadata["versions"][0].items()
               if not key.startswith("download_") and key != "install_size"}
    version.update(version=args.version, status=args.status)
    metadata["versions"] = [version]
    payload = package_payload(root, identifier, args.version)
    version["install_size"] = sum(map(len, payload.values()))
    payload["metadata.json"] = json_bytes(metadata)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data, compresslevel=9)
    archive_bytes = buffer.getvalue()
    basename = f"Flori-KiCad-Library-{args.version}"
    release_url = f"https://github.com/{repository}/releases/download/v{args.version}"
    external_metadata = copy.deepcopy(metadata)
    external_metadata["versions"][0].update(
        download_url=f"{release_url}/{basename}.zip",
        download_sha256=digest(archive_bytes), download_size=len(archive_bytes),
    )
    previous = {"packages": []}
    if args.previous_packages:
        previous = json.loads(args.previous_packages.read_text(encoding="utf-8"))
    elif args.previous_packages_url:
        if not args.previous_packages_url.startswith("https://"):
            parser.error("上一版索引 URL 必须使用 HTTPS")
        try:
            with urlopen(args.previous_packages_url, timeout=30) as response:
                previous = json.load(response)
        except HTTPError as error:
            if error.code != 404:
                raise
            print("未找到上一版公开索引，生成首版索引。")
    packages = previous["packages"]
    old = [package for package in packages if package["identifier"] == identifier]
    if len(old) > 1:
        raise ValueError("上一版索引含有重复的包标识")
    history = old[0]["versions"] if old else []
    if any(version_key(item) == version_key(version) for item in history):
        raise ValueError(f"版本已发布，不能覆盖：{args.version}")
    if args.status == "stable" and any(
        item["status"] == "stable" and version_key(item) >= version_key(version)
        for item in history
    ):
        raise ValueError("稳定版本必须高于索引中已有的稳定版本")
    external_metadata["versions"].extend(history)
    external_metadata["versions"].sort(key=version_key, reverse=True)
    catalog = json_bytes({"packages": [package for package in packages
                                      if package["identifier"] != identifier] + [external_metadata]})
    now = datetime.now(timezone.utc)
    index_url = (f"https://github.com/{repository}/releases/latest/download"
                 if args.status == "stable" else release_url)
    repository_json = json_bytes({
        "$schema": "https://go.kicad.org/pcm/schemas/v2",
        "schema_version": 2, "name": "Flori KiCad Library",
        "maintainer": metadata["author"],
        "packages": {"url": f"{index_url}/packages.json", "sha256": digest(catalog),
                     "update_timestamp": int(now.timestamp()),
                     "update_time_utc": now.strftime("%Y-%m-%d %H:%M:%S")},
    })
    notes = (
        f"# Flori KiCad Library {args.version}\n\n"
        f"发布状态：`{args.status}`；需要 KiCad 10。\n\n"
        f"下载 `{basename}.zip`，在 PCM 中选择“从文件安装”。"
        "安装后可在包的 resources 目录阅读 INSTALL_zh.md；旧工程兼容脚本按需执行。\n\n"
        f"PCM 订阅入口：{index_url}/repository.json\n\n"
        "详细变更请参阅对应标签的 Git 提交记录。\n"
    )
    if args.source_commit:
        notes += (f"\n源码提交：[{args.source_commit[:7]}]"
                  f"(https://github.com/{repository}/commit/{args.source_commit})\n")
    outputs = {
        f"{basename}.zip": archive_bytes,
        f"{basename}.sha256": f"{digest(archive_bytes)}  {basename}.zip\n".encode(),
        f"{basename}.metadata.json": json_bytes(external_metadata),
        "packages.json": catalog, "repository.json": repository_json,
        "release-notes.md": notes.encode("utf-8"),
    }
    destination = args.output_dir.resolve() / args.version
    if any((destination / name).exists() for name in outputs):
        raise FileExistsError(f"输出文件已存在，请使用新的输出目录：{destination}")
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        temporary = destination / (name + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(destination / name)
    print(f"PCM 包已生成：{destination / (basename + '.zip')}")
    print(f"文件数：{len(payload)}；SHA-256：{digest(archive_bytes)}")


if __name__ == "__main__":
    main()
