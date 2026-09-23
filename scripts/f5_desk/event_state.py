"""Committed event registry snapshot reader — scripts/f5_desk (NEWS_PROTOCOL writer wire).

SAFE READ-ONLY. Fail-open callers must wrap imports/calls in try/except.
Desk reference: /workspace/gtos/live/news_protocol/event_state.py
Hooks: book_owner._f5_new_risk_block; order_router.place pre-open_trade.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Prefer VPS committed registry under judgment\live (OWNER wire 20260907).
DEFAULT_REGISTRY = Path(
    r"host-local\redacted_host\repo\judgment\live\event_registry_v1.json"
)


def _candidate_registry_paths():
    here = Path(__file__).resolve()
    # scripts/f5_desk/event_state.py -> repo = parents[2]
    repo = here.parents[2] if len(here.parents) >= 3 else here.parent
    out = []
    env = os.environ.get("GTOS_EVENT_REGISTRY")
    if env:
        out.append(Path(env))
    out.extend(
        [
            DEFAULT_REGISTRY,
            repo / "judgment" / "live" / "event_registry_v1.json",
            repo / "live" / "event_registry_v1.json",
            repo / "data" / "event_registry_v1.json",
            repo / "judgment" / "state" / "event_registry_v1.json",
            Path(r"host-local\redacted_host\repo\live\event_registry_v1.json"),
            Path("/workspace/gtos/live/event_registry_v1.json"),
        ]
    )
    return out


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_registry_path(path: Optional[Path] = None) -> Path:
    if path is not None:
        return Path(path)
    for cand in _candidate_registry_paths():
        if cand.exists():
            return cand
    return Path(DEFAULT_REGISTRY)


def load_registry(path: Optional[Path] = None) -> dict:
    path = resolve_registry_path(path)
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError("registry_not_a_mapping")
    if not isinstance(obj.get("events"), list):
        raise ValueError("registry_events_unavailable")
    version = (
        obj.get("event_version")
        or obj.get("as_of_utc")
        or hashlib.sha256(raw).hexdigest()[:16]
    )
    return {
        "ok": True,
        "path": str(path),
        "event_version": version,
        "as_of_utc": obj.get("as_of_utc"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "n_events": len(obj.get("events") or []),
        "registry": obj,
        "checked_at_utc": _utc_now_iso(),
    }


def committed_snapshot(path: Optional[Path] = None) -> dict:
    """Compact snapshot suitable for pre-send annotation (no broker I/O)."""
    loaded = load_registry(path)
    events = (loaded.get("registry") or {}).get("events") or []
    compact = []
    issues = []
    for ev in events:
        if not isinstance(ev, dict):
            issues.append({"error": "registry_event_not_a_mapping", "row": ev})
            continue
        compact.append(
            {
                "occurrence_id": ev.get("occurrence_id"),
                "scheduled_utc": ev.get("scheduled_utc"),
                "window_t15_utc": ev.get("window_t15_utc"),
                "window_t60_end_utc": ev.get("window_t60_end_utc"),
                "affected_instruments": ev.get("affected_instruments"),
                "official_high": ev.get("official_high"),
                "event_class": ev.get("event_class"),
            }
        )
    return {
        "event_version": loaded["event_version"],
        "checked_at_utc": loaded["checked_at_utc"],
        "path": loaded["path"],
        "sha256": loaded["sha256"],
        "n_events": loaded["n_events"],
        "events": compact,
        "applied": False,
        "snapshot_read": True,
        "writer_loaded": False,
        "issues": issues,
    }


def canonical_symbol(symbol: str) -> str:
    """Explicit FTMO cash alias; do not guess arbitrary broker suffixes."""
    value = str(symbol or "").strip().upper()
    if value.endswith(".CASH"):
        value = value[:-5]
    return value.replace(".", "").replace("_", "").replace(" ", "")


def parse_utc(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("event_timezone_missing")
    return parsed.astimezone(timezone.utc)


def active_exclusions(
    *, now: Optional[datetime] = None, symbol: Optional[str] = None,
    path: Optional[Path] = None, snapshot: Optional[dict] = None,
) -> list[dict]:
    """Decide on the exact bytes already annotated, at the supplied current clock.

    Invalid rows remain explicit issues; they cannot erase another valid HIGH
    exclusion or become a fabricated healthy empty calendar.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("decision_timezone_missing")
    snap = snapshot if snapshot is not None else committed_snapshot(path)
    issues = snap.setdefault("issues", [])
    out = []
    for ev in snap["events"]:
        try:
            if ev.get("official_high") is not True:
                if ev.get("official_high") is None:
                    issues.append({"occurrence_id": ev.get("occurrence_id"), "error": "official_high_unknown"})
                continue
            start, end = parse_utc(ev.get("window_t15_utc")), parse_utc(ev.get("window_t60_end_utc"))
            if end <= start:
                raise ValueError("invalid_event_window")
            instruments = ev.get("affected_instruments")
            if not isinstance(instruments, list) or not instruments:
                raise ValueError("event_instrument_scope_unknown")
            if symbol is not None and canonical_symbol(symbol) not in {canonical_symbol(i) for i in instruments}:
                continue
            # End is exclusive: the same exact instant activates the T+60 request.
            if start <= now < end:
                out.append({**ev, "in_window": True})
        except (TypeError, ValueError, AttributeError) as exc:
            issues.append({"occurrence_id": ev.get("occurrence_id") if isinstance(ev, dict) else None,
                           "error": str(exc)})
    return out


if __name__ == "__main__":
    try:
        print(json.dumps(committed_snapshot(), indent=2)[:2000])
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "registry_missing",
                    "detail": str(exc),
                    "applied": False,
                },
                indent=2,
            )
        )
