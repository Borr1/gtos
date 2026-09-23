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
    w7_hit, f5_hit, w7_pre, w7_post, f5_pre, f5_post = _window_flags(exported, covering)
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
        "w7_pre_block_minutes": w7_pre,
        "w7_post_block_minutes": w7_post,
        "f5_pre_block_minutes": f5_pre,
        "f5_post_block_minutes": f5_post,
        "symbol": symbol,
        "usd_high_in_10d": len(usd_high) if covering else 0,
    }


def _event_facts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "events": [
            {
                "minutes_from_as_of": int(row["minutes_from_as_of"]),
                "currency": row.get("currency"),
                "event": row.get("event"),
            }
            for row in rows
        ]
    }


def _window_flags(
    exported: list[dict[str, Any]],
    covering: bool,
) -> tuple[bool | None, bool | None, int | None, int | None, int | None, int | None]:
    """W7 and F5 window flags.

    Off the Challenge writer the minute comparisons stand and the block
    widths stay on the card. On it, two concurrent choices. An empty
    answer is None and does not restore the minute comparison. No HIGH
    event means the flag is false without an ask. The nearby-day slice
    stays a card cut, not a decision.
    """
    legacy_w7 = (
        any(
            -W7_POST <= int(row["minutes_from_as_of"]) <= W7_PRE
            and row["currency"] in {"USD", "XAU"}
            for row in exported
        )
        if covering
        else None
    )
    legacy_f5 = (
        any(-F5_POST <= int(row["minutes_from_as_of"]) <= F5_PRE for row in exported)
        if covering
        else None
    )
    try:
        from src.judgment.state_choices import LEGACY, on_challenge, window_bool
    except Exception:
        return legacy_w7, legacy_f5, W7_PRE, W7_POST, F5_PRE, F5_POST
    if not on_challenge():
        return legacy_w7, legacy_f5, W7_PRE, W7_POST, F5_PRE, F5_POST
    if not covering:
        return None, None, None, None, None, None

    w7_rows = [row for row in exported if row.get("currency") in {"USD", "XAU"}]

    def _flag(chosen: Any) -> bool | None:
        if chosen is LEGACY or chosen is None:
            return None
        if chosen is True or chosen is False:
            return chosen
        return None

    w7_chosen: Any = False if not w7_rows else None
    f5_chosen: Any = False if not exported else None
    jobs: list[tuple[str, Any]] = []
    if w7_rows:
        jobs.append(("w7", w7_rows))
    if exported:
        jobs.append(("f5", exported))
    if jobs:
        from concurrent.futures import ThreadPoolExecutor

        def _ask(item: tuple[str, list[dict[str, Any]]]) -> tuple[str, Any]:
            kind, rows = item
            if kind == "w7":
                return kind, window_bool(
                    "news.high_in_w7_window",
                    _event_facts(rows),
                    "Is a USD or gold high-impact event inside the block window for this as-of?",
                )
            return kind, window_bool(
                "news.high_in_f5_window",
                _event_facts(rows),
                "Is a high-impact event inside the block window for this as-of?",
            )

        try:
            with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
                for kind, chosen in pool.map(_ask, jobs):
                    if kind == "w7":
                        w7_chosen = chosen
                    else:
                        f5_chosen = chosen
        except Exception:
            w7_chosen = None if w7_rows else False
            f5_chosen = None if exported else False
    return _flag(w7_chosen), _flag(f5_chosen), None, None, None, None
