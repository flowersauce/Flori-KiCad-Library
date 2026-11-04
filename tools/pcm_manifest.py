"""共用 PCM 输入清单：收集包内容，并判断 Git 推送是否影响构建。"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
from pathlib import Path, PurePosixPath


MANIFEST_PATH = "tools/pcm-inputs.json"


def validate_path(value: str) -> None:
    """清单只接受仓库内的 POSIX 相对路径或 glob。"""
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError(f"无效清单路径：{value!r}")


def has_magic(value: str) -> bool:
    return any(character in value for character in "*?[")


def load_manifest(root: Path) -> dict:
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    if manifest["schema_version"] != 1:
        raise ValueError("不支持的 PCM 输入清单版本")
    validate_path(manifest["metadata"])
    if has_magic(manifest["metadata"]):
        raise ValueError("元数据必须指定单个文件")
    for rule in manifest["files"]:
        validate_path(rule["source"])
        if "target" in rule:
            validate_path(rule["target"])
            if has_magic(rule["source"]) or has_magic(rule["target"]):
                raise ValueError("显式目标路径只能用于单个文件")
        if "json_remove" in rule and has_magic(rule["source"]):
            raise ValueError("JSON 字段转换只能用于单个文件")
    for pattern in manifest["build_inputs"]:
        validate_path(pattern)
    return manifest


def matches_path(path: str, pattern: str) -> bool:
    """逐级匹配路径；* 不跨目录，** 匹配零级或多级目录。"""
    parts, patterns = path.split("/"), pattern.split("/")

    def match(position: int, index: int) -> bool:
        if index == len(patterns):
            return position == len(parts)
        if patterns[index] == "**":
            return any(match(next_position, index + 1)
                       for next_position in range(position, len(parts) + 1))
        return (position < len(parts)
                and fnmatch.fnmatchcase(parts[position], patterns[index])
                and match(position + 1, index + 1))

    return match(0, 0)


def matches_rule(path: str, rule: dict) -> bool:
    return (matches_path(path, rule["source"])
            and ("suffixes" not in rule
                 or PurePosixPath(path).suffix.lower() in rule["suffixes"]))


def affects_package(manifest: dict, path: str) -> bool:
    """不读取变更文件，因此被删除或重命名的旧路径也可以命中。"""
    return (path in (MANIFEST_PATH, manifest["metadata"])
            or any(matches_rule(path, rule) for rule in manifest["files"])
            or any(matches_path(path, pattern) for pattern in manifest["build_inputs"]))


def collect_files(root: Path, manifest: dict) -> dict[str, bytes]:
    """收集清单文件，统一处理重命名复制、JSON 转换和路径越界检查。"""
    root = root.resolve()
    outputs: dict[str, bytes] = {}
    for rule in manifest["files"]:
        paths = sorted(root.glob(rule["source"]))
        if not has_magic(rule["source"]) and not (root / rule["source"]).is_file():
            raise FileNotFoundError(f"缺少打包输入：{rule['source']}")
        for path in paths:
            relative = path.relative_to(root).as_posix()
            if not path.is_file() or not matches_rule(relative, rule):
                continue
            if not path.resolve().is_relative_to(root):
                raise ValueError(f"资源链接指向仓库外：{path}")
            target = rule.get("target", relative)
            if target.split("/", 1)[0] not in {"symbols", "footprints", "3dmodels", "resources"}:
                raise ValueError(f"包内文件必须放在 PCM 库内容目录：{target}")
            if target in outputs:
                raise ValueError(f"重复的包内路径：{target}")
            data = path.read_bytes()
            if "json_remove" in rule:
                record = json.loads(data)
                for field in rule["json_remove"]:
                    record.pop(field, None)
                data = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            outputs[target] = data
    return outputs


def changed_paths(root: Path, base: str, head: str) -> list[str]:
    """关闭重命名合并，保留两侧路径；NUL 分隔兼容空格、换行和中文文件名。"""
    if base.startswith("-") or head.startswith("-"):
        raise ValueError("Git 版本不能以选项前缀开头")
    result = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", "-z", base, head, "--"],
        cwd=root, capture_output=True, check=True,
    )
    return [name for name in result.stdout.decode("utf-8", errors="surrogateescape").split("\0") if name]


def should_build(root: Path, manifest: dict, event_name: str, event: dict) -> bool:
    if event_name != "push":
        print("PR、手动触发或未知事件：保留打包检查。")
        return True
    base, head = event.get("before", ""), event.get("after", "")
    if not base or not head or set(base) == {"0"}:
        print("新分支或缺少比较基线：保守执行打包。")
        return True
    try:
        paths = changed_paths(root, base, head)
    except subprocess.CalledProcessError:
        print("无法读取完整 Git 差异（例如强制推送的旧提交缺失）：保守执行打包。")
        return True
    matches = [path for path in paths if affects_package(manifest, path)]
    print(f"变更文件：{len(paths)}；影响 PCM 的文件：{len(matches)}")
    return bool(matches)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="本地预览使用的 Git 比较基线")
    parser.add_argument("--head", default="HEAD", help="本地预览使用的 Git 目标版本")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root)
    if args.base:
        event_name = "push"
        event = {"before": args.base, "after": args.head}
    else:
        event_name = os.environ.get("GITHUB_EVENT_NAME", "")
        event_file = os.environ.get("GITHUB_EVENT_PATH")
        event = json.loads(Path(event_file).read_text(encoding="utf-8")) if event_file else {}
    build = should_build(root, manifest, event_name, event)
    value = "true" if build else "false"
    print(f"build={value}")
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"build={value}\n")


if __name__ == "__main__":
    main()
