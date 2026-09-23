"""Controlled Codex memory retrieval for GTOS Context OS."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from src.gtos_context_os.catalog import query_terms


DEFAULT_MEMORY_ROOT = Path.home() / ".codex" / "memories"
DEFAULT_MEMORY_FILES = (
    "memory_summary.md",
    "MEMORY.md",
)


def memory_files(memory_root: Path | str = DEFAULT_MEMORY_ROOT, *, include_ad_hoc: bool = True) -> list[Path]:
    root = Path(memory_root or DEFAULT_MEMORY_ROOT).expanduser()
    files: list[Path] = []
    for rel in DEFAULT_MEMORY_FILES:
        path = root / rel
        if path.exists() and path.is_file():
            files.append(path)
    if include_ad_hoc:
        notes = root / "extensions" / "ad_hoc" / "notes"
        if notes.exists():
            files.extend(sorted(path for path in notes.glob("*.md") if path.is_file()))
    return files


def search_memory(
    query: str,
    *,
    memory_root: Path | str | None = DEFAULT_MEMORY_ROOT,
    limit: int = 8,
    include_ad_hoc: bool = True,
) -> list[dict[str, Any]]:
    terms = query_terms(query)
    if not terms:
        return []
    hits: list[tuple[int, dict[str, Any]]] = []
    root = Path(memory_root or DEFAULT_MEMORY_ROOT).expanduser()
    for path in memory_files(root, include_ad_hoc=include_ad_hoc):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lower = text.lower()
        if not all(term in lower for term in terms):
            continue
        score = sum(lower.count(term) for term in terms)
        rel = _safe_relative(path, root)
        hits.append(
            (
                -score,
                {
                    "path": f"codex_memory/{rel}",
                    "abs_path": path.as_posix(),
                    "title": _title(path, text),
                    "score": score,
                    "authority_tier": "bronze_chat_or_memory",
                    "evidence_class": "memory_registry_context",
                    "freshness": "memory_derived_verify_against_current_disk",
                    "doc_type": "codex_memory",
                    "route": None,
                    "size_bytes": path.stat().st_size,
                    "sha256": None,
                    "content_status": "memory_text_indexed",
                    "snippet": _best_snippet(text, terms),
                },
            )
        )
    hits.sort(key=lambda item: (item[0], str(item[1]["path"])))
    return [item for _, item in hits[:limit]]


def _safe_relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("#").strip()[:220] or path.name
    return path.name


def _best_snippet(text: str, terms: Iterable[str], *, radius: int = 420) -> str:
    lower = text.lower()
    first = min((lower.find(term) for term in terms if lower.find(term) >= 0), default=0)
    start = max(0, first - radius)
    end = min(len(text), first + radius)
    snippet = text[start:end]
    snippet = re.sub(r"\n{3,}", "\n\n", snippet)
    return snippet.strip()
