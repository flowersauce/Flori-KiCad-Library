"""Small source-span helpers for KiCad library files and library tables."""

from __future__ import annotations

import itertools
import json
import re
from pathlib import Path


TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()"]+')


def child_spans(text: str, root_name: str) -> tuple[list[tuple[int, int]], int]:
    """Locate direct children without rewriting quoted text or nested expressions."""
    if not re.match(r"\s*\(" + re.escape(root_name) + r"\b", text):
        raise ValueError(f"Expected a {root_name} expression")
    depth = 0
    start = 0
    closing = -1
    spans: list[tuple[int, int]] = []
    for token in TOKEN.finditer(text):
        if token.group() == "(":
            if depth == 0 and closing >= 0:
                raise ValueError("Multiple root expressions")
            depth += 1
            if depth == 2:
                start = token.start()
        elif token.group() == ")":
            if depth == 2:
                spans.append((start, token.end()))
            elif depth == 1:
                closing = token.start()
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced expression")
    if depth != 0 or closing < 0:
        raise ValueError("Incomplete expression")
    return spans, closing


def string_value(token: re.Match[str]) -> str:
    """Read a KiCad atom or a quoted string."""
    value = token.group()
    return json.loads(value) if value.startswith('"') else value


def field_token(text: str, field: str) -> re.Match[str]:
    """Find a direct table-entry field while respecting quoted strings."""
    children, _ = child_spans(text, "lib")
    for start, end in children:
        tokens = list(itertools.islice(TOKEN.finditer(text, start, end), 3))
        if len(tokens) == 3 and tokens[1].group() == field:
            return tokens[2]
    raise ValueError(f"Library entry has no {field} field")


def symbol_blocks(path: Path) -> tuple[str, dict[str, str]]:
    """Read a symbol-library header and the unchanged top-level symbol bodies."""
    text = path.read_text(encoding="utf-8-sig")
    children, _ = child_spans(text, "kicad_symbol_lib")
    blocks: dict[str, str] = {}
    first_symbol = None
    for start, end in children:
        tokens = list(itertools.islice(TOKEN.finditer(text, start, end), 3))
        if len(tokens) != 3 or tokens[1].group() != "symbol":
            continue
        name = string_value(tokens[2])
        if name in blocks:
            raise ValueError(f"Duplicate symbol in {path}: {name}")
        if first_symbol is None:
            first_symbol = start
        blocks[name] = text[start:end]
    if first_symbol is None:
        raise ValueError(f"No symbols in {path}")
    return text[:first_symbol].rstrip(), blocks


def merge_library_table(original: bytes, table_name: str, libraries: dict[str, str]) -> bytes:
    """Add or repoint selected nicknames, retaining every unrelated row."""
    text = original.decode("utf-8-sig")
    spans, closing = child_spans(text, table_name)
    edits: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    newline = "\r\n" if b"\r\n" in original else "\n"
    for start, end in spans:
        entry = text[start:end]
        if not re.match(r"\(\s*lib\b", entry):
            continue
        nickname = string_value(field_token(entry, "name"))
        if nickname not in libraries:
            continue
        if nickname in seen:
            raise ValueError(f"Duplicate library nickname: {nickname}")
        seen.add(nickname)
        if string_value(field_token(entry, "type")) != "KiCad":
            raise ValueError(f"Nickname {nickname} is used by a non-KiCad library")
        uri = field_token(entry, "uri")
        if string_value(uri) != libraries[nickname]:
            edits.append((start + uri.start(), start + uri.end(), json.dumps(libraries[nickname])))
    additions = []
    for name, uri in libraries.items():
        if name in seen:
            continue
        description = "Legacy compatibility alias" if name.startswith(
            ("Flowersauce_", "PCM_Flowersauce_")
        ) else ""
        additions.append(
            f'\t(lib (name {json.dumps(name)}) (type "KiCad") '
            f'(uri {json.dumps(uri)}) (options "") (descr {json.dumps(description)})){newline}'
        )
    if additions:
        separator = "" if text[:closing].endswith(("\n", "\r")) else newline
        edits.append((closing, closing, separator + "".join(additions)))
    if not edits:
        return original
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + value + text[end:]
    encoding = "utf-8-sig" if original.startswith(b"\xef\xbb\xbf") else "utf-8"
    return text.encode(encoding)
