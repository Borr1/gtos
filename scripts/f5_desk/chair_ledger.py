"""Persist original stops and the 22:00 UTC day baseline. No MT5.

A lock must never overwrite an original. After a restart the desk and the book
both read these files so R is not recomputed against a BE stop.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from scripts.f5_desk import chair_card as card
from scripts.f5_desk import common

LEDGER_NAME = "chair_orig_sl.json"
BASELINE_NAME = "chair_day_baseline.json"
WAKE_NAME = "chair_wake.json"
LAST_SIT_NAME = "chair_last_sit.json"
HEALTH_NAME = "chair_health.json"


def state_dir(repo_root: Path, namespace: str = common.NAMESPACE) -> Path:
    return common.judgment_state_dir(repo_root, namespace) / "state"


def orig_path(repo_root: Path, namespace: str = common.NAMESPACE) -> Path:
    return state_dir(repo_root, namespace) / LEDGER_NAME


def baseline_path(repo_root: Path, namespace: str = common.NAMESPACE) -> Path:
    return state_dir(repo_root, namespace) / BASELINE_NAME


def _tickets(doc: Any) -> dict[str, float]:
    if not isinstance(doc, dict):
        return {}
    raw = doc.get("tickets") if isinstance(doc.get("tickets"), dict) else doc
    out: dict[str, float] = {}
    if not isinstance(raw, dict):
        return out
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def load_orig_ledger(path: Path) -> dict[str, float]:
    return _tickets(common.read_json(path, default={}))


def persist_orig_sl(
    path: Path,
    ticket: object,
    side: str,
    entry: object,
    live_sl: object,
    stored: object = None,
) -> Optional[float]:
    """Latch a risk-side original. Refuse a lock. Never overwrite a kept orig."""
    if ticket in (None, 0, ""):
        return None
    key = str(int(ticket)) if str(ticket).isdigit() else str(ticket)
    current = load_orig_ledger(path)
    if key in current:
        kept = card.latch_orig_sl(side, entry, live_sl, current[key])
        return kept
    latched = card.latch_orig_sl(side, entry, live_sl, stored)
    if latched is None:
        return None
    current[key] = float(latched)
    common.write_json_atomic(path, {
        "tickets": current,
        "updated_utc": common.iso_utc(),
    })
    return float(latched)


def persist_positions(
    path: Path,
    positions: list[Mapping[str, Any]],
) -> dict[str, float]:
    """Latch orig from a snapshot's positions. Existing keys stay."""
    for pos in positions:
        persist_orig_sl(
            path,
            pos.get("ticket"),
            str(pos.get("side") or ""),
            pos.get("entry") or pos.get("entry_price") or pos.get("price_open"),
            pos.get("sl") or pos.get("stop_now") or pos.get("stop_loss"),
            pos.get("orig_sl") or pos.get("stop_prev"),
        )
    return load_orig_ledger(path)


def load_baseline(path: Path) -> Optional[float]:
    doc = common.read_json(path, default=None)
    if not isinstance(doc, dict):
        return None
    try:
        value = float(doc.get("balance"))
    except (TypeError, ValueError):
        return None
    return value


def persist_baseline(path: Path, balance: float, reset_utc: str) -> None:
    common.write_json_atomic(path, {
        "balance": float(balance),
        "reset_utc": reset_utc,
    })


def ftmo_reset_utc(now: datetime) -> datetime:
    """The last 22:00 UTC reset at or before ``now``."""
    now = now.astimezone(timezone.utc)
    reset = now.replace(hour=22, minute=0, second=0, microsecond=0)
    if now < reset:
        from datetime import timedelta
        reset = reset - timedelta(days=1)
    return reset


def maybe_roll_baseline(
    path: Path,
    balance_now: float,
    now: Optional[datetime] = None,
) -> float:
    """If the stored reset is older than the last 22:00 UTC, take ``balance_now``."""
    now = now or common.now_utc()
    want = ftmo_reset_utc(now)
    doc = common.read_json(path, default=None)
    stored_reset = None
    stored_bal = None
    if isinstance(doc, dict):
        stored_reset = common.parse_utc(doc.get("reset_utc"))
        try:
            stored_bal = float(doc.get("balance"))
        except (TypeError, ValueError):
            stored_bal = None
    if stored_reset is not None and stored_reset >= want and stored_bal is not None:
        return stored_bal
    persist_baseline(path, balance_now, common.iso_utc(want))
    return float(balance_now)


def write_trade_record_orig(
    repo_root: Path,
    ticket: object,
    orig_sl: float,
    namespace: str = common.NAMESPACE,
) -> bool:
    """Write ``f5_original_stop`` once onto the book's trade record. Never overwrite."""
    if ticket in (None, 0, ""):
        return False
    rec_path = (
        Path(repo_root) / "pipeline_state" / "ultimate_book" / namespace
        / "trade_records" / f"{int(ticket)}.json"
    )
    rec = common.read_json(rec_path, default=None)
    if not isinstance(rec, dict):
        return False
    inst = rec.get("instrumentation")
    if not isinstance(inst, dict):
        inst = {}
        rec["instrumentation"] = inst
    if inst.get("f5_original_stop") not in (None, ""):
        return False
    inst["f5_original_stop"] = float(orig_sl)
    return common.write_json_atomic(rec_path, rec)
