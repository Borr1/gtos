"""WMB ENFORCE 2 — scoped 2-stop day remint circuit (Chair 2026-09-21).

After 2 same-symbol same-sleeve stop-class closes in a session day, hard-refuse
remint until next session for two_bar / rejection_wick / isolated_spike.

Isolated re-entry after >=15m remains for OTHER sleeves. Does not place/flatten.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional

REASON = "wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops"
TARGET_FAMILY_SUBSTR = ("two_bar", "rejection_wick", "isolated_spike")


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def sleeve_in_2stop_scope(sleeve: str) -> bool:
    sl = _norm(sleeve)
    return any(tok in sl for tok in TARGET_FAMILY_SUBSTR)


def _is_stop_class(row: dict) -> bool:
    ex = _norm(row.get("exit_class") or row.get("exit") or "")
    if "orig_stop" in ex or ex in ("sl", "stop", "stop_loss"):
        return True
    ca = _norm(row.get("close_action") or row.get("reason") or "")
    if "orig_stop" in ca or ca in ("sl", "stop", "stop_loss"):
        return True
    # conservative: lossy broker_closed for scoped sleeves counts toward remint bleed
    if "broker_closed" in ca:
        try:
            r = float(row.get("realised_r") if row.get("realised_r") is not None else row.get("realized_r") or 0)
            if r < 0:
                return True
        except Exception:
            pass
    return False


def count_orig_stops_today(
    rows: Iterable[dict],
    *,
    symbol: str,
    sleeve: str,
    session_day: str,
) -> int:
    sy, sl, day = _norm(symbol), _norm(sleeve), str(session_day or "")[:10]
    n = 0
    for r in rows or []:
        try:
            if _norm(r.get("symbol")) != sy:
                continue
            if _norm(r.get("sleeve")) != sl:
                continue
            d = str(r.get("decision_day") or r.get("session_day") or r.get("day") or "")[:10]
            if not d:
                cu = str(r.get("closed_utc") or r.get("closed_at") or "")
                d = cu[:10]
            if d != day:
                continue
            if _is_stop_class(r):
                n += 1
        except Exception:
            continue
    return n


def refuse_reason(
    *,
    symbol: str,
    sleeve: str,
    session_day: str,
    orig_stop_rows: Iterable[dict],
    threshold: int = 2,
) -> Optional[str]:
    if not sleeve_in_2stop_scope(sleeve):
        return None
    n = count_orig_stops_today(
        orig_stop_rows, symbol=symbol, sleeve=sleeve, session_day=session_day
    )
    if n >= int(threshold):
        return (
            f"{REASON}:n={n}:threshold={threshold}:"
            f"symbol={_norm(symbol)}:sleeve={_norm(sleeve)}:day={str(session_day)[:10]}"
        )
    return None


def load_just_closed_rows(repo_root: str | Path) -> list[dict]:
    p = Path(repo_root) / "judgment" / "live" / "just_closed_siblings.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        rows = list(data.get("closed") or [])
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def refuse_reason_live(
    *,
    repo_root: str | Path,
    symbol: str,
    sleeve: str,
    session_day: str,
    threshold: int = 2,
) -> Optional[str]:
    return refuse_reason(
        symbol=symbol,
        sleeve=sleeve,
        session_day=session_day,
        orig_stop_rows=load_just_closed_rows(repo_root),
        threshold=threshold,
    )


def smoke_import() -> dict[str, Any]:
    demo = [
        {"symbol": "XAUUSD", "sleeve": "dsp_two_bar_thrust_into_20high_continues", "decision_day": "2026-09-17", "exit_class": "orig_stop"},
        {"symbol": "XAUUSD", "sleeve": "dsp_two_bar_thrust_into_20high_continues", "decision_day": "2026-09-17", "exit_class": "orig_stop"},
    ]
    r = refuse_reason(
        symbol="XAUUSD",
        sleeve="dsp_two_bar_thrust_into_20high_continues",
        session_day="2026-09-17",
        orig_stop_rows=demo,
    )
    return {"ok": bool(r and r.startswith(REASON)), "reason": r}
