"""Load HIGH-event spines. Fail-closed. Never invent events.

Reads every JSON spine under ``data/news/`` plus the June operator file
``data/news_calendar.json``. An as-of with no covering event still yields
``spine_empty=True`` — that is honesty, not “no HIGH.”
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPINES = (
    REPO_ROOT / "data" / "news_calendar.json",
    REPO_ROOT / "data" / "news",
)

W7_PRE = 15
W7_POST = 2
F5_PRE = 15
F5_POST = 60


def _parse_iso(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _event_dt(row: dict[str, Any]) -> datetime | None:
    # Host f5_high_calendar.v1 uses scheduled_utc; FF this-week uses datetime_utc.
    for key in ("datetime_utc", "scheduled_utc", "date"):
        if key in row and "T" in str(row.get(key, "")):
            parsed = _parse_iso(str(row[key]))
            if parsed is not None:
                return parsed
    date = str(row.get("date") or "").strip()
    tod = str(row.get("time_utc") or row.get("time") or "").strip()
    if date and tod:
        return _parse_iso(f"{date}T{tod}:00Z" if len(tod) <= 5 else f"{date}T{tod}Z")
    if date:
        return _parse_iso(f"{date}T00:00:00Z")
    return None


def _normalize_event(row: dict[str, Any], *, source: str) -> dict[str, Any] | None:
    dt = _event_dt(row)
    if dt is None:
        return None
    impact = str(row.get("impact") or row.get("Impact") or "").upper()
    if impact in {"HIGH", "RED"}:
        impact = "HIGH"
    elif impact in {"MEDIUM", "ORANGE"}:
        impact = "MEDIUM"
    elif impact in {"LOW", "YELLOW"}:
        impact = "LOW"
    title = str(row.get("event") or row.get("title") or row.get("name") or "").strip()
    currency = str(row.get("currency") or row.get("country") or "").strip().upper()
    if currency in {"US", "USA", "UNITED STATES"}:
        currency = "USD"
    host_axis = "f5_high_calendar" in source
    return {
        "datetime_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": title,
        "impact": impact or "UNKNOWN",
        "currency": currency,
        "source": source,
        "event_type": row.get("event_type"),
        "official_high": bool(row.get("official_high")) if row.get("official_high") is not None else host_axis,
        "time_certainty": row.get("time_certainty"),
        "challenge_axis": host_axis,
        "_dt": dt,
    }


def _iter_json_files(paths: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".json":
            out.append(path)
        elif path.is_dir():
            out.extend(sorted(path.glob("*.json")))
    return out


def load_spines(paths: Iterable[Path] | None = None) -> dict[str, Any]:
    files = _iter_json_files(paths if paths is not None else DEFAULT_SPINES)
    events: list[dict[str, Any]] = []
    sources: list[str] = []
    digest = hashlib.sha256()
    for file in files:
        raw = file.read_bytes()
        digest.update(raw)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rel = str(file.relative_to(REPO_ROOT)) if file.is_relative_to(REPO_ROOT) else str(file)
        sources.append(rel)
        rows: list[dict[str, Any]]
        if isinstance(payload, list):
            rows = [r for r in payload if isinstance(r, dict)]
        elif isinstance(payload, dict):
            inner = payload.get("events") or payload.get("items") or []
            rows = [r for r in inner if isinstance(r, dict)]
        else:
            continue
        for row in rows:
            normalized = _normalize_event(row, source=rel)
            if normalized is not None:
                events.append(normalized)
    events = _dedup_events(events)
    events.sort(key=lambda e: e["_dt"])
    return {
        "spine_id": digest.hexdigest() if files else None,
        "sources": sources,
        "events": events,
        "n_files": len(files),
        "n_challenge_axis": sum(1 for e in events if e.get("challenge_axis")),
    }


def _dedup_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer host Challenge-axis rows when datetime+currency collide."""
    best: dict[tuple[str, str, str], dict[str, Any]] = {}
    for event in events:
        key = (
            event["datetime_utc"],
            event.get("currency") or "",
            (event.get("event_type") or event.get("event") or "").lower(),
        )
        prev = best.get(key)
        if prev is None:
            best[key] = event
            continue
        if event.get("challenge_axis") and not prev.get("challenge_axis"):
            best[key] = event
        elif event.get("official_high") and not prev.get("official_high"):
            best[key] = event
    return list(best.values())


def attach_news(
    as_of_utc: datetime,
    *,
    spines: dict[str, Any] | None = None,
    symbol: str = "XAUUSD",
) -> dict[str, Any]:
    packed = spines if spines is not None else load_spines()
    as_of = as_of_utc.astimezone(timezone.utc)
    window_days = timedelta(days=10)
    nearby = [
        e
        for e in packed["events"]
        if abs((e["_dt"] - as_of).total_seconds()) <= window_days.total_seconds()
    ]
    high = [e for e in nearby if e["impact"] == "HIGH"]
    # XAUUSD W7 map is USD-only; still expose all HIGH so F5 can see GBP/JPY speakers.
    usd_high = [e for e in high if e["currency"] in {"USD", "XAU", "ALL"}]
    covering = bool(nearby)
    challenge_axis_nearby = [e for e in nearby if e.get("challenge_axis")]
    exported = []
    for e in high:
        minutes = int(round((e["_dt"] - as_of).total_seconds() / 60.0))
        exported.append(
            {
                "datetime_utc": e["datetime_utc"],
                "event": e["event"],
                "impact": e["impact"],
                "currency": e["currency"],
                "minutes_from_as_of": minutes,
                "event_type": e.get("event_type"),
                "official_high": e.get("official_high"),
                "time_certainty": e.get("time_certainty"),
                "challenge_axis": bool(e.get("challenge_axis")),
            }
        )
    nearest = None
    if high:
        nearest_e = min(high, key=lambda e: abs((e["_dt"] - as_of).total_seconds()))
        nearest = int(round((nearest_e["_dt"] - as_of).total_seconds() / 60.0))
    w7_hit = any(
        -W7_POST <= int(e["minutes_from_as_of"]) <= W7_PRE
        and e["currency"] in {"USD", "XAU"}
        for e in exported
    ) if covering else None
    f5_hit = any(
        -F5_POST <= int(e["minutes_from_as_of"]) <= F5_PRE
        for e in exported
    ) if covering else None
    return {
        "spine_id": packed["spine_id"],
        "spine_extracted_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spine_empty": not covering,
        "challenge_axis_covering": bool(challenge_axis_nearby),
        "n_challenge_axis_nearby": len(challenge_axis_nearby),
        "source": "w7_news_filter_json" if packed["sources"] else "unassembled",
        "sources": packed["sources"],
        "events": exported,
        "minutes_to_nearest_high": nearest if covering else None,
        "high_in_w7_window": w7_hit,
        "high_in_f5_window": f5_hit,
        "w7_pre_block_minutes": W7_PRE,
        "w7_post_block_minutes": W7_POST,
        "f5_pre_block_minutes": F5_PRE,
        "f5_post_block_minutes": F5_POST,
        "symbol": symbol,
        "usd_high_in_10d": len(usd_high) if covering else 0,
    }
