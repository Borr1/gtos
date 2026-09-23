"""Session capsule helpers for preserving useful work without raw chat replay."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Sequence

from src.gtos_context_os.catalog import utc_now


DEFAULT_SESSION_CAPSULE_DIR = Path(".context/context_os/session_capsules")


def create_session_capsule(
    title: str,
    summary: str,
    *,
    task: str = "",
    sources: Sequence[str] = (),
    commands: Sequence[str] = (),
    decisions: Sequence[str] = (),
    repo: Path | str = ".",
    out_dir: Path | str = DEFAULT_SESSION_CAPSULE_DIR,
) -> Path:
    repo_path = Path(repo).resolve()
    target_dir = repo_path / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    payload = {
        "schema_version": "gtos_context_session_capsule_v1",
        "generated_at_utc": generated_at,
        "title": title,
        "task": task,
        "summary": summary,
        "sources": list(sources),
        "commands": list(commands),
        "decisions": list(decisions),
        "status": "local_session_capsule_not_canonical_until_promoted",
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    path = target_dir / f"{generated_at.replace(':', '').replace('-', '')}-{_slug(title)}-{digest}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def list_session_capsules(
    *,
    repo: Path | str = ".",
    out_dir: Path | str = DEFAULT_SESSION_CAPSULE_DIR,
    limit: int = 5,
    task_query: str | None = None,
) -> list[dict[str, Any]]:
    """Return recent local continuity capsules.

    Capsules are compact continuity breadcrumbs, not canonical proof.  They are
    useful after compaction, laptop restarts, or agent pool churn because they
    preserve what was done, which sources were touched, and what still needs
    current-disk verification.
    """

    repo_path = Path(repo).resolve()
    target_dir = repo_path / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
    if not target_dir.exists():
        return []
    query_terms = _query_terms(task_query or "")
    capsules: list[dict[str, Any]] = []
    for path in sorted(target_dir.glob("*.json"), reverse=True):
        capsule = _read_capsule(path, repo_path)
        if capsule is None:
            continue
        if query_terms and not _capsule_matches(capsule, query_terms):
            continue
        capsules.append(capsule)
        if len(capsules) >= limit:
            break
    return capsules


def session_capsule_status(
    *,
    repo: Path | str = ".",
    out_dir: Path | str = DEFAULT_SESSION_CAPSULE_DIR,
    limit: int = 5,
) -> dict[str, Any]:
    repo_path = Path(repo).resolve()
    target_dir = repo_path / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
    capsules = list_session_capsules(repo=repo_path, out_dir=target_dir, limit=limit)
    latest = capsules[0] if capsules else None
    return {
        "schema_version": "gtos_context_session_capsule_status_v1",
        "root": target_dir.as_posix(),
        "exists": target_dir.exists(),
        "count": _count_capsules(target_dir),
        "returned": len(capsules),
        "latest": latest,
        "continuity_status": "has_recent_capsules" if latest else "no_session_capsules_found",
        "use_boundary": "local_continuity_hint_verify_against_current_disk",
    }


def _read_capsule(path: Path, repo_path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    stat = path.stat()
    try:
        rel = path.relative_to(repo_path).as_posix()
    except ValueError:
        rel = path.as_posix()
    return {
        "path": rel,
        "abs_path": path.as_posix(),
        "mtime_ns": stat.st_mtime_ns,
        "schema_version": payload.get("schema_version"),
        "generated_at_utc": payload.get("generated_at_utc"),
        "title": payload.get("title") or path.stem,
        "task": payload.get("task") or "",
        "summary": payload.get("summary") or "",
        "sources": list(payload.get("sources") or []),
        "commands": list(payload.get("commands") or []),
        "decisions": list(payload.get("decisions") or []),
        "status": payload.get("status") or "local_session_capsule_not_canonical_until_promoted",
        "freshness": "session_capsule_verify_against_current_disk",
    }


def _count_capsules(target_dir: Path) -> int:
    if not target_dir.exists():
        return 0
    return sum(1 for _ in target_dir.glob("*.json"))


def _query_terms(query: str) -> list[str]:
    return [term.lower() for term in re.findall(r"[A-Za-z0-9_./:-]+", query) if len(term) > 1]


def _capsule_matches(capsule: dict[str, Any], terms: Sequence[str]) -> bool:
    haystack = "\n".join(
        [
            str(capsule.get("path") or ""),
            str(capsule.get("title") or ""),
            str(capsule.get("task") or ""),
            str(capsule.get("summary") or ""),
            " ".join(str(item) for item in capsule.get("sources") or []),
            " ".join(str(item) for item in capsule.get("decisions") or []),
        ]
    ).lower()
    return all(term in haystack for term in terms)


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")[:64] or "session"
