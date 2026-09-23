"""Fold optional context-desk files into a slate. Never blocks a trade.

A missing, stale, or unreadable brief is ``present=false``. The chair may
read these; they are not verdicts and they never HOLD a candidate.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.f5_desk import common

BRIEF_NAMES = ("macro.md", "calendar_delta.json", "ops_questions.md")


def _header_times(text: str) -> tuple[str | None, str | None]:
    as_of = None
    valid = None
    for line in (text or "").splitlines()[:12]:
        low = line.strip().lower().replace(" ", "")
        if low.startswith("as_of_utc:") or low.startswith("as_of_utc="):
            as_of = line.split(":", 1)[-1].split("=", 1)[-1].strip()
        if low.startswith("valid_until_utc:") or low.startswith("valid_until_utc="):
            valid = line.split(":", 1)[-1].split("=", 1)[-1].strip()
    return as_of, valid


def _fresh(valid_until: str | None, now: datetime) -> bool:
    parsed = common.parse_utc(valid_until)
    if parsed is None:
        return False
    return parsed > now


def fold_one(path: Path, now: datetime) -> dict[str, Any]:
    if not path.is_file():
        return {"name": path.name, "present": False, "stale": False}
    try:
        if path.suffix == ".json":
            doc = common.read_json(path, default=None)
            if not isinstance(doc, dict):
                return {"name": path.name, "present": False, "stale": True, "error": "unreadable"}
            as_of = doc.get("as_of_utc")
            valid = doc.get("valid_until_utc")
            fresh = _fresh(str(valid) if valid else None, now)
            return {
                "name": path.name,
                "present": True,
                "stale": not fresh,
                "as_of_utc": as_of,
                "valid_until_utc": valid,
                "adds": len(doc.get("adds") or []) if isinstance(doc.get("adds"), list) else None,
                "breaking": len(doc.get("breaking") or []) if isinstance(doc.get("breaking"), list) else None,
            }
        text = path.read_text(encoding="utf-8", errors="replace")
        as_of, valid = _header_times(text)
        fresh = _fresh(valid, now)
        return {
            "name": path.name,
            "present": True,
            "stale": not fresh,
            "as_of_utc": as_of,
            "valid_until_utc": valid,
            "chars": len(text),
        }
    except Exception as exc:  # noqa: BLE001 — briefs must never raise
        return {"name": path.name, "present": False, "stale": True, "error": str(exc)[:120]}


def fold_desk_briefs(briefs_dir: Path, now: datetime | None = None) -> dict[str, Any]:
    """Context only. Absent by default. Never a trade instruction."""
    now = now or common.now_utc()
    root = Path(briefs_dir)
    files = [fold_one(root / name, now) for name in BRIEF_NAMES]
    structure_dir = root / "structure"
    structure = []
    if structure_dir.is_dir():
        for path in sorted(structure_dir.glob("*.md")):
            structure.append(fold_one(path, now))
    present = [f for f in files + structure if f.get("present")]
    stale = [f["name"] for f in present if f.get("stale")]
    return {
        "present": bool(present),
        "stale_names": stale,
        "files": files,
        "structure": structure,
        "note": "context only; never a hold or a take",
    }
