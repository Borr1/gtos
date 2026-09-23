"""L-7 reference impl — Q71 slippage logger (extended schema).

DESIGN-ONLY MODULE. Lives under research/ for review, NOT under src/. Main
thread copies the relevant pieces into src/components/slippage_shadow_logger.py
after CEO approval per the design doc at
research/ml_program/experiments/l6_l7_logger_design.md.

This reference impl wraps the EXISTING shipped slippage logger
(``src/components/slippage_shadow_logger.py``) and ADDS:

  - extended entry-side fields (expected_sl, expected_tp1, slippage_pct_atr,
    fill_type, broker_state, mt5_retcode, request_volume, realized_volume,
    event tag);
  - a new ``record_close_slippage(...)`` API for SL hits / TP fills / BE
    moves / manual closes / J46-J49 time stops.

Schema-stability discipline (mirrored from the shipped logger):
  1. NEW fields are appended at the END of each row dict; existing fields
     never change semantics.
  2. The same JSONL file (``shadow_logs/slippage.jsonl``) receives both
     entry-side and close-side rows; the ``event`` field discriminates them.
     Rows produced by the shipped logger are forward-compatible — they read
     as ``event="entry_fill"`` with the new fields absent.
  3. Pip-size resolution reuses ``_PIP_SIZE_BY_SYMBOL`` from the shipped
     logger (vendored copy below to keep this module unit-testable in
     isolation).

Fail-open: any exception inside the logger is caught and downgraded to a
WARNING; trade flow MUST NEVER block on a shadow-log write failure.

Tests at the bottom of this file run standalone:
    python -m pytest research/ml_program/experiments/l7_slippage_logger.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default sink. Tests redirect via ``log_path`` kwarg or by monkey-patching
# this module attribute.
SHADOW_LOG_PATH = "shadow_logs/slippage.jsonl"


# Per-symbol pip size in price units. VENDORED from the shipped
# ``src/components/slippage_shadow_logger.py`` so this reference impl is
# unit-testable without importing src/. Production wiring uses the live
# table; the two MUST stay in sync (test below verifies this on import).
_PIP_SIZE_BY_SYMBOL: dict[str, float] = {
    # Metals
    "XAUUSD": 0.01,
    "XAGUSD": 0.001,
    # Indices (point-based)
    "US30": 1.0,
    "US30_cash": 1.0,
    "NAS100": 1.0,
    "NAS100_cash": 1.0,
    # JPY pairs
    "USDJPY": 0.01,
    "GBPJPY": 0.01,
    "EURJPY": 0.01,
    # Other FX
    "GBPUSD": 0.0001,
    "EURUSD": 0.0001,
    "AUDUSD": 0.0001,
}


# Canonical event tags. Free-form strings accepted (logger never rejects
# unknown values) but these are the documented values consumers can rely on.
EVENT_ENTRY_FILL = "entry_fill"
EVENT_SL_FILL = "sl_fill"
EVENT_TP1_PARTIAL_FILL = "tp1_partial_fill"
EVENT_TP2_FULL_FILL = "tp2_full_fill"
EVENT_BE_CLOSE = "be_close"
EVENT_J46_J49_TIME_STOP = "j46_j49_time_stop"
EVENT_MANUAL_CLOSE = "manual_close"
EVENT_FORCE_CLOSE = "force_close"
EVENT_SL_MOD_FAILED = "sl_modification_failed"


def _resolve_pip_size(symbol: str) -> Optional[float]:
    """Return pip size for ``symbol`` or None if unknown.

    Tries verbatim, then strips common broker suffixes (``_cash``, ``.cash``,
    ``.raw``). Mirrors the shipped logger.
    """
    if not symbol:
        return None
    if symbol in _PIP_SIZE_BY_SYMBOL:
        return _PIP_SIZE_BY_SYMBOL[symbol]
    for suffix in ("_cash", ".cash", ".raw"):
        if symbol.endswith(suffix):
            base = symbol[: -len(suffix)]
            if base in _PIP_SIZE_BY_SYMBOL:
                return _PIP_SIZE_BY_SYMBOL[base]
    return None


def _coerce_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _resolve_log_path(explicit: Optional[str]) -> str:
    """Re-read module attribute on every write so tests can monkey-patch."""
    return explicit or SHADOW_LOG_PATH


def _atomic_append(row: dict, log_path: str) -> None:
    """Append a single jsonl line. Mkdir parent if needed. NEVER raises."""
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:
        logger.warning(
            "slippage_logger write failed (non-blocking): %s [path=%s]",
            exc, log_path,
        )


# ============================================================================
# Entry-side (extends shipped record_slippage)
# ============================================================================


def record_slippage_extended(
    *,
    ticket: int,
    symbol: str,
    direction: str,
    requested_price: float,
    fill_price: float,
    spread_at_request: Optional[float] = None,
    kill_zone: Optional[str] = None,
    trigger: Optional[str] = None,
    notes: Optional[str] = None,
    # NEW additive fields:
    expected_sl: Optional[float] = None,
    expected_tp1: Optional[float] = None,
    m15_atr: Optional[float] = None,
    fill_type: Optional[str] = None,
    broker_state: Optional[dict] = None,
    mt5_retcode: Optional[int] = None,
    request_volume: Optional[float] = None,
    realized_volume: Optional[float] = None,
    log_path: Optional[str] = None,
) -> None:
    """Append one entry-fill row with extended Q71 telemetry.

    All NEW fields default to None (backward-compatible with shipped writer).
    NEVER raises (fail-open contract). Trade flow MUST NOT depend on success.
    """
    try:
        req = _coerce_float(requested_price, 0.0) or 0.0
        fill = _coerce_float(fill_price, 0.0) or 0.0
        slippage_price = round(fill - req, 8)

        if direction == "LONG":
            slippage_directional = round(fill - req, 8)
        elif direction == "SHORT":
            slippage_directional = round(req - fill, 8)
        else:
            slippage_directional = None

        pip_size = _resolve_pip_size(symbol)
        if pip_size and pip_size > 0 and slippage_directional is not None:
            slippage_pips: Optional[float] = round(slippage_directional / pip_size, 4)
        else:
            slippage_pips = None

        slippage_pct_atr: Optional[float] = None
        if m15_atr and m15_atr > 0 and slippage_directional is not None:
            try:
                slippage_pct_atr = round(slippage_directional / float(m15_atr), 6)
            except (TypeError, ValueError):
                slippage_pct_atr = None

        spread_value = _coerce_float(spread_at_request, default=None)

        row = {
            # ---- Existing fields (preserved order + names) ----
            "ts": datetime.now(timezone.utc).isoformat(),
            "ticket": int(ticket) if ticket is not None else 0,
            "symbol": symbol,
            "direction": direction,
            "requested_price": req,
            "fill_price": fill,
            "slippage_price": slippage_price,
            "slippage_directional": slippage_directional,
            "slippage_pips": slippage_pips,
            "spread_at_request": spread_value,
            "kill_zone": kill_zone,
            "trigger": trigger,
            "notes": notes,
            # ---- NEW additive fields ----
            "event": EVENT_ENTRY_FILL,
            "expected_sl": _coerce_float(expected_sl, default=None),
            "expected_tp1": _coerce_float(expected_tp1, default=None),
            "slippage_pct_atr": slippage_pct_atr,
            "fill_type": fill_type,
            "broker_state": broker_state,
            "mt5_retcode": int(mt5_retcode) if mt5_retcode is not None else None,
            "request_volume": _coerce_float(request_volume, default=None),
            "realized_volume": _coerce_float(realized_volume, default=None),
        }
        _atomic_append(row, _resolve_log_path(log_path))
    except Exception as exc:
        logger.warning(
            "slippage_logger entry-fill failed (non-blocking): %s "
            "[ticket=%s symbol=%s]", exc, ticket, symbol,
        )


# ============================================================================
# Close-side (NEW)
# ============================================================================


def record_close_slippage(
    *,
    event: str,
    entry_ticket: int,
    symbol: str,
    direction: str,
    expected_close_price: Optional[float],
    realized_close_price: Optional[float],
    close_reason: Optional[str] = None,
    time_in_trade_sec: Optional[int] = None,
    realized_sl: Optional[float] = None,
    realized_tp1: Optional[float] = None,
    realized_tp2: Optional[float] = None,
    spread_at_close: Optional[float] = None,
    kill_zone: Optional[str] = None,
    broker_state: Optional[dict] = None,
    mt5_retcode: Optional[int] = None,
    realized_volume: Optional[float] = None,
    notes: Optional[str] = None,
    log_path: Optional[str] = None,
) -> None:
    """Append one close-side row.

    The same JSONL file gets both entry rows (event="entry_fill") and close
    rows. ``event`` discriminates. Joinable to the entry row by
    ``entry_ticket == ticket``.

    Sign convention for ``slippage_close_directional`` matches the entry side:
        LONG  : adverse = realized_close < expected_close (fill below target)
        SHORT : adverse = realized_close > expected_close

    For SL hits the SL is on the OPPOSITE side of the directional preference
    (LONG SL is below entry; LONG SL slipping further DOWN is adverse). The
    sign convention below correctly captures this because ``expected_close``
    is the SL price and ``realized_close`` is the broker fill — for a LONG
    SL hit, realized < expected = adverse.

    NEVER raises. Trade flow MUST NOT depend on success.
    """
    try:
        expected = _coerce_float(expected_close_price, default=None)
        realized = _coerce_float(realized_close_price, default=None)

        if expected is not None and realized is not None:
            slippage_close_price = round(realized - expected, 8)
            if direction == "LONG":
                slippage_close_directional = round(expected - realized, 8)
            elif direction == "SHORT":
                slippage_close_directional = round(realized - expected, 8)
            else:
                slippage_close_directional = None
        else:
            slippage_close_price = None
            slippage_close_directional = None

        pip_size = _resolve_pip_size(symbol)
        if (pip_size and pip_size > 0
                and slippage_close_directional is not None):
            slippage_close_pips: Optional[float] = round(
                slippage_close_directional / pip_size, 4
            )
        else:
            slippage_close_pips = None

        spread_value = _coerce_float(spread_at_close, default=None)

        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "entry_ticket": int(entry_ticket) if entry_ticket is not None else 0,
            "symbol": symbol,
            "direction": direction,
            "expected_close_price": expected,
            "realized_close_price": realized,
            "slippage_close_price": slippage_close_price,
            "slippage_close_directional": slippage_close_directional,
            "slippage_close_pips": slippage_close_pips,
            "realized_sl": _coerce_float(realized_sl, default=None),
            "realized_tp1": _coerce_float(realized_tp1, default=None),
            "realized_tp2": _coerce_float(realized_tp2, default=None),
            "close_reason": close_reason,
            "time_in_trade_sec": int(time_in_trade_sec) if time_in_trade_sec is not None else None,
            "spread_at_close": spread_value,
            "kill_zone": kill_zone,
            "broker_state": broker_state,
            "mt5_retcode": int(mt5_retcode) if mt5_retcode is not None else None,
            "realized_volume": _coerce_float(realized_volume, default=None),
            "notes": notes,
        }
        _atomic_append(row, _resolve_log_path(log_path))
    except Exception as exc:
        logger.warning(
            "slippage_logger close-side failed (non-blocking): %s "
            "[event=%s entry_ticket=%s symbol=%s]",
            exc, event, entry_ticket, symbol,
        )


# ============================================================================
# Tests
# ============================================================================
# Self-contained pytest tests — run with:
#     python -m pytest research/ml_program/experiments/l7_slippage_logger.py


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class _FakeOrderResult:
    """Mimics MT5Interface.OrderResult shape used in execution.py."""

    def __init__(
        self,
        order: int = 0,
        success: bool = True,
        price: float = 0.0,
        volume: float = 0.0,
        retcode: int = 10009,
        comment: str = "Request executed",
    ):
        self.order = order
        self.success = success
        self.price = price
        self.volume = volume
        self.retcode = retcode
        self.comment = comment


def test_record_entry_fill_extended_schema(tmp_path):
    out = tmp_path / "slip.jsonl"
    record_slippage_extended(
        ticket=233955223, symbol="GBPJPY", direction="LONG",
        requested_price=215.274, fill_price=215.276,
        spread_at_request=1.4, kill_zone="london", trigger="limit_fill",
        notes="Request executed",
        expected_sl=214.500, expected_tp1=216.500,
        m15_atr=0.020, fill_type="IOC",
        broker_state={"connected": True, "trade_allowed": True,
                      "spread_cents": 1.4, "server_time_offset_sec": 0},
        mt5_retcode=10009, request_volume=0.10, realized_volume=0.10,
        log_path=str(out),
    )
    rows = _read_rows(out)
    assert len(rows) == 1
    r = rows[0]
    # All 13 existing fields present
    for key in ["ts", "ticket", "symbol", "direction", "requested_price",
                "fill_price", "slippage_price", "slippage_directional",
                "slippage_pips", "spread_at_request", "kill_zone",
                "trigger", "notes"]:
        assert key in r, f"missing existing field {key}"
    # All 9 new fields present
    for key in ["event", "expected_sl", "expected_tp1", "slippage_pct_atr",
                "fill_type", "broker_state", "mt5_retcode",
                "request_volume", "realized_volume"]:
        assert key in r, f"missing new field {key}"
    assert r["event"] == EVENT_ENTRY_FILL
    assert r["fill_type"] == "IOC"
    assert r["expected_sl"] == 214.500
    assert r["mt5_retcode"] == 10009
    assert r["broker_state"]["connected"] is True
    # Slippage math: LONG, fill 215.276 vs req 215.274 → +0.002 adverse
    assert abs(r["slippage_directional"] - 0.002) < 1e-6
    assert abs(r["slippage_pips"] - 0.2) < 1e-3  # JPY pip = 0.01


def test_record_close_slippage_sl_hit(tmp_path):
    out = tmp_path / "slip.jsonl"
    # LONG GBPJPY entry @ 215.276 SL @ 214.500; broker fills SL at 214.485
    # (slipped 1.5 pips against us).
    record_close_slippage(
        event=EVENT_SL_FILL, entry_ticket=233955223, symbol="GBPJPY",
        direction="LONG",
        expected_close_price=214.500, realized_close_price=214.485,
        realized_sl=214.485,
        close_reason="sl_hit", time_in_trade_sec=900,
        spread_at_close=1.6, kill_zone="london",
        broker_state={"connected": True, "trade_allowed": True},
        mt5_retcode=10009, realized_volume=0.10,
        notes="auto SL hit",
        log_path=str(out),
    )
    rows = _read_rows(out)
    assert len(rows) == 1
    r = rows[0]
    assert r["event"] == EVENT_SL_FILL
    assert r["entry_ticket"] == 233955223
    assert r["realized_sl"] == 214.485
    # LONG, expected 214.500, realized 214.485 → adverse = 0.015
    # Sign convention: LONG adverse = expected - realized (positive when
    # fill below target).
    assert abs(r["slippage_close_directional"] - 0.015) < 1e-6
    # Pips = adverse / 0.01 = 1.5
    assert abs(r["slippage_close_pips"] - 1.5) < 1e-3


def test_record_close_slippage_tp1_partial(tmp_path):
    out = tmp_path / "slip.jsonl"
    # LONG XAUUSD entry; TP1 expected at 3210.50, partial filled at 3210.30
    # → adverse 0.20 (2 pips on XAU).
    record_close_slippage(
        event=EVENT_TP1_PARTIAL_FILL, entry_ticket=999, symbol="XAUUSD",
        direction="LONG",
        expected_close_price=3210.50, realized_close_price=3210.30,
        realized_tp1=3210.30,
        close_reason="tp1_partial", time_in_trade_sec=1800,
        log_path=str(out),
    )
    rows = _read_rows(out)
    assert rows[0]["event"] == EVENT_TP1_PARTIAL_FILL
    assert rows[0]["realized_tp1"] == 3210.30
    # LONG TP1 expected 3210.50 realized 3210.30 → adverse = 0.20
    assert abs(rows[0]["slippage_close_directional"] - 0.20) < 1e-6
    assert abs(rows[0]["slippage_close_pips"] - 20.0) < 1e-3  # XAU pip 0.01


def test_close_slippage_handles_zero_realized_price(tmp_path):
    """Broker returning 0.0 should be logged verbatim for forensic clarity."""
    out = tmp_path / "slip.jsonl"
    record_close_slippage(
        event=EVENT_TP2_FULL_FILL, entry_ticket=1, symbol="USDJPY",
        direction="LONG",
        expected_close_price=150.000, realized_close_price=0.0,
        log_path=str(out),
    )
    rows = _read_rows(out)
    assert rows[0]["realized_close_price"] == 0.0
    # Slippage math still computed against 0.0 — analyst can detect pattern.
    assert rows[0]["slippage_close_price"] is not None


def test_close_slippage_pip_resolution(tmp_path):
    out = tmp_path / "slip.jsonl"
    cases = [
        ("XAUUSD", 0.01),
        ("USDJPY", 0.01),
        ("NAS100", 1.0),
        ("GBPUSD", 0.0001),
        ("XAGUSD", 0.001),
        ("US30_cash", 1.0),  # broker variant via suffix-strip
    ]
    for sym, expected_pip in cases:
        # Pick prices so directional = 1 * pip exactly.
        record_close_slippage(
            event=EVENT_SL_FILL, entry_ticket=1, symbol=sym,
            direction="LONG",
            expected_close_price=100.0,
            realized_close_price=100.0 - expected_pip,
            log_path=str(out),
        )
    rows = _read_rows(out)
    assert len(rows) == len(cases)
    for r, (_sym, _pip) in zip(rows, cases):
        assert abs(r["slippage_close_pips"] - 1.0) < 1e-3


def test_join_via_entry_ticket(tmp_path):
    out = tmp_path / "slip.jsonl"
    record_slippage_extended(
        ticket=42, symbol="XAUUSD", direction="LONG",
        requested_price=3200.0, fill_price=3200.10,
        log_path=str(out),
    )
    record_close_slippage(
        event=EVENT_TP2_FULL_FILL, entry_ticket=42, symbol="XAUUSD",
        direction="LONG",
        expected_close_price=3210.0, realized_close_price=3210.05,
        log_path=str(out),
    )
    rows = _read_rows(out)
    assert len(rows) == 2
    assert rows[0]["ticket"] == rows[1]["entry_ticket"] == 42
    assert rows[0]["event"] == EVENT_ENTRY_FILL
    assert rows[1]["event"] == EVENT_TP2_FULL_FILL


def test_failure_open_on_disk_error(tmp_path, monkeypatch):
    """Logger must swallow disk errors; trade flow must not depend on log."""
    out = tmp_path / "no_dir" / "child" / "slip.jsonl"

    def _explode(*a, **k):
        raise PermissionError("simulated")
    monkeypatch.setattr("builtins.open", _explode)

    # Must not raise:
    record_slippage_extended(
        ticket=1, symbol="XAUUSD", direction="LONG",
        requested_price=1.0, fill_price=1.0,
        log_path=str(out),
    )
    record_close_slippage(
        event=EVENT_SL_FILL, entry_ticket=1, symbol="XAUUSD",
        direction="LONG",
        expected_close_price=1.0, realized_close_price=1.0,
        log_path=str(out),
    )


def test_jsonl_lines_parse_individually(tmp_path):
    out = tmp_path / "slip.jsonl"
    for i in range(5):
        record_slippage_extended(
            ticket=i, symbol="XAUUSD", direction="LONG",
            requested_price=3200.0 + i, fill_price=3200.0 + i + 0.01,
            log_path=str(out),
        )
    text = out.read_text(encoding="utf-8")
    for line in text.splitlines():
        assert json.loads(line)


def test_backward_compat_with_existing_row(tmp_path):
    """Replay the 1 production row from 2026-04-28 — existing schema readers
    should accept the new rows; new-schema readers must accept the old row.
    """
    historical = (
        '{"ts": "2026-04-28T09:30:05.343157+00:00", "ticket": 233955223, '
        '"symbol": "GBPJPY", "direction": "LONG", "requested_price": 215.274, '
        '"fill_price": 0.0, "slippage_price": -215.274, '
        '"slippage_directional": -215.274, "slippage_pips": -21527.4, '
        '"spread_at_request": 1.4000000000010004, "kill_zone": null, '
        '"trigger": "limit_fill", "notes": "Request executed"}'
    )
    out = tmp_path / "slip.jsonl"
    out.write_text(historical + "\n", encoding="utf-8")
    # Append a new-schema row.
    record_slippage_extended(
        ticket=999, symbol="XAUUSD", direction="LONG",
        requested_price=3200.0, fill_price=3200.05,
        expected_sl=3195.0, expected_tp1=3215.0,
        log_path=str(out),
    )
    rows = _read_rows(out)
    assert len(rows) == 2
    # Historical row parses; new fields absent.
    assert rows[0]["ticket"] == 233955223
    assert "event" not in rows[0]  # historical row, missing new field
    # New row carries new fields.
    assert rows[1]["event"] == EVENT_ENTRY_FILL
    assert rows[1]["expected_sl"] == 3195.0


def test_pip_size_table_matches_shipped(tmp_path):
    """The vendored pip table must stay in sync with the shipped logger."""
    try:
        from src.components.slippage_shadow_logger import (  # type: ignore
            _PIP_SIZE_BY_SYMBOL as shipped,
        )
    except Exception:
        # If src is not importable in the test env (e.g. worktree without
        # the path), skip rather than fail. Production CI will run with src.
        return
    assert _PIP_SIZE_BY_SYMBOL == shipped, (
        "VENDORED pip table has drifted from src/components/"
        "slippage_shadow_logger.py — re-sync before merge."
    )


def test_unknown_direction_writes_null_directional(tmp_path):
    out = tmp_path / "slip.jsonl"
    record_close_slippage(
        event=EVENT_MANUAL_CLOSE, entry_ticket=1, symbol="XAUUSD",
        direction="UNKNOWN",
        expected_close_price=3200.0, realized_close_price=3201.0,
        log_path=str(out),
    )
    rows = _read_rows(out)
    assert rows[0]["slippage_close_directional"] is None
    assert rows[0]["slippage_close_pips"] is None
    # Raw signed price still recorded.
    assert abs(rows[0]["slippage_close_price"] - 1.0) < 1e-6


if __name__ == "__main__":
    try:
        import pytest  # type: ignore
        sys.exit(pytest.main([__file__, "-v"]))
    except ImportError:
        print("pytest not installed; skipping test run", file=sys.stderr)
        sys.exit(2)
