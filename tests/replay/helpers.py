"""Replay-test helpers — reconstruction, schema-drift handling, path discovery.

Keep src/ untouched; all helpers live here. Every reconstruction is
best-effort: if a record has an unexpected field the helper returns None
and the caller skips it rather than crashing the test session.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

# Ensure src/ is importable regardless of test invocation cwd.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.models.analysis_models import PrimaryAnalysisOutput
from src.models.market_state_models import MarketStateObject


SYMBOLS = ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD")


# ---------------------------------------------------------------------------
# Path discovery
# ---------------------------------------------------------------------------


def repo_root() -> Path:
    """Return project root."""
    return _REPO_ROOT


def live_evaluations_dir(symbol: Optional[str] = None) -> Path:
    base = _REPO_ROOT / "knowledge_base" / "live_evaluations"
    return base / symbol if symbol else base


def trade_records_dir(symbol: Optional[str] = None) -> Path:
    base = _REPO_ROOT / "knowledge_base" / "trade_records"
    return base / symbol if symbol else base


def historical_csv(symbol: str, timeframe: str) -> Path:
    return _REPO_ROOT / "data" / "historical_2026" / f"{symbol}_{timeframe}.csv"


# ---------------------------------------------------------------------------
# Live evaluation rows (thin metadata — no MSO)
# ---------------------------------------------------------------------------


def _parse_date_from_filename(path: Path) -> Optional[datetime]:
    """Extract YYYY-MM-DD date from '2026-04-19.jsonl' style filenames."""
    name = path.stem
    try:
        return datetime.strptime(name, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def iter_live_eval_rows(
    window_days: int = 30,
    symbols: Optional[tuple] = None,
    now: Optional[datetime] = None,
) -> Iterator[dict]:
    """Yield live_evaluations rows within the last ``window_days``.

    Filters out rows whose file is older than ``window_days`` from ``now``
    (default: utcnow()). Malformed lines are skipped (with a stderr warning
    one-line summary) rather than crashing.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now.timestamp() - window_days * 86400
    symbols = symbols or SYMBOLS
    skipped = 0

    for sym in symbols:
        sym_dir = live_evaluations_dir(sym)
        if not sym_dir.exists():
            continue
        for fp in sorted(sym_dir.glob("*.jsonl")):
            file_date = _parse_date_from_filename(fp)
            if file_date and file_date.timestamp() < cutoff:
                continue
            try:
                with fp.open(encoding="utf-8") as f:
                    for lineno, raw in enumerate(f, start=1):
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            row = json.loads(raw)
                        except json.JSONDecodeError:
                            skipped += 1
                            continue
                        # Add file-origin metadata so downstream can trace.
                        row["_source_file"] = str(fp.relative_to(_REPO_ROOT))
                        row["_source_line"] = lineno
                        yield row
            except OSError:
                # File vanished between glob and open (live log rotation).
                continue

    if skipped:
        print(f"[replay.helpers] skipped {skipped} malformed live_eval rows",
              file=sys.stderr)


# ---------------------------------------------------------------------------
# Trade records (full fidelity: MSO + AI output + decision pipeline)
# ---------------------------------------------------------------------------


def _extract_trade_record_date(record: dict, filepath: Path) -> Optional[datetime]:
    """Extract the record's timestamp from metadata.candle_time or filename."""
    ct = (record.get("metadata") or {}).get("candle_time")
    if ct:
        try:
            return datetime.fromisoformat(ct.replace("Z", "+00:00"))
        except ValueError:
            pass
    # Fall back to filename prefix, e.g. "2026-04-15_ny_1415.json".
    try:
        date_str = filepath.stem.split("_")[0]
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def iter_trade_records(
    window_days: int = 30,
    symbols: Optional[tuple] = None,
    now: Optional[datetime] = None,
    require_mso: bool = False,
) -> Iterator[dict]:
    """Yield full trade_records dicts within ``window_days``.

    Each yield adds ``_source_file`` and ``_candle_time_dt`` for convenience.
    Skips records that fail to parse as JSON, or (when ``require_mso``) lack
    a valid MSO block.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now.timestamp() - window_days * 86400
    symbols = symbols or SYMBOLS
    skipped = 0

    for sym in symbols:
        sym_dir = trade_records_dir(sym)
        if not sym_dir.exists():
            continue
        for fp in sorted(sym_dir.glob("*.json")):
            try:
                with fp.open(encoding="utf-8") as f:
                    rec = json.load(f)
            except (json.JSONDecodeError, OSError):
                skipped += 1
                continue
            dt = _extract_trade_record_date(rec, fp)
            if dt is None:
                skipped += 1
                continue
            if dt.timestamp() < cutoff:
                continue
            if require_mso and not (rec.get("mso") or {}).get("timeframes"):
                skipped += 1
                continue
            rec["_source_file"] = str(fp.relative_to(_REPO_ROOT))
            rec["_candle_time_dt"] = dt
            yield rec

    if skipped:
        print(f"[replay.helpers] skipped {skipped} trade_record files "
              "(parse error / missing MSO / missing timestamp)",
              file=sys.stderr)


# ---------------------------------------------------------------------------
# Pydantic reconstruction (defensive against schema drift)
# ---------------------------------------------------------------------------


def reconstruct_mso(record: dict) -> Optional[MarketStateObject]:
    """Rebuild a MarketStateObject from a trade_record's ``mso`` block.

    Returns None (not raise) on schema drift / validation error — callers
    decide whether to skip the row or use a partial dict.
    """
    mso_dict = record.get("mso")
    if not isinstance(mso_dict, dict):
        return None
    try:
        return MarketStateObject(**mso_dict)
    except Exception:  # noqa: BLE001 — defensive; schema drift tolerated
        return None


def reconstruct_pa(record: dict) -> Optional[PrimaryAnalysisOutput]:
    """Rebuild a PrimaryAnalysisOutput from a trade_record's ``ai_response`` block."""
    ar = record.get("ai_response")
    if not isinstance(ar, dict):
        return None
    try:
        return PrimaryAnalysisOutput(**ar)
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Historical OHLCV (for identify_structure tests)
# ---------------------------------------------------------------------------


def load_ohlcv_csv(symbol: str, timeframe: str) -> list[dict]:
    """Load CSV bars. Returns [{'time', 'open', 'high', 'low', 'close', ...}]."""
    fp = historical_csv(symbol, timeframe)
    if not fp.exists():
        return []
    rows: list[dict] = []
    with fp.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append({
                    "time": row["time"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0) or 0),
                })
            except (ValueError, KeyError):
                continue
    return rows


def rolling_windows(bars: list[dict], window: int, step: int) -> Iterator[list[dict]]:
    """Yield non-overlapping (or step-spaced) rolling windows of size ``window``."""
    if len(bars) < window:
        return
    for i in range(window, len(bars) + 1, step):
        yield bars[i - window : i]


# ---------------------------------------------------------------------------
# Minimal mock MT5 for Gate 3 invocation (no real broker dependency)
# ---------------------------------------------------------------------------


class MockTick:
    def __init__(self, spread_cents: float = 10.0):
        self.spread_cents = spread_cents


class MockMT5:
    """Enough surface for check_permissions — is_connected/get_tick/positions_get."""

    def __init__(self, connected: bool = True, spread_cents: float = 10.0):
        self._connected = connected
        self._spread = spread_cents

    def is_connected(self) -> bool:
        return self._connected

    def get_tick(self, symbol: str):  # noqa: ARG002
        return MockTick(self._spread)

    def positions_get(self, **kwargs):  # noqa: ARG002
        return []


# ---------------------------------------------------------------------------
# Default config surface for invariance tests
# ---------------------------------------------------------------------------


DEFAULT_REPLAY_CONFIG: dict = {
    "deployment": {"phase": 3},
    "risk": {
        "max_daily_loss_pct": 4.0,
        "risk_per_trade_pct": 2.0,
        "max_spread_cents": 300.0,
        "sl_buffer_dollars": 0.02,
        "max_concurrent": 2,
    },
    "verification": {
        "enabled": True,
        "ob_price_tolerance_pct": 0.002,
        "log_warnings": False,
    },
    "model_a": {
        "enabled_frameworks": ["ob_retest"],
        "displacement_min_ratio": 1.5,
    },
    "gate1": {
        "min_rr": 1.5,
        "ob_retest_sl_exception": True,
        "ob_retest_sl_min_buffer_atr": 0.3,
        "sl_liquidity_cluster_enabled": False,
        "sl_liquidity_cluster_margin_atr": 0.5,
    },
    "pre_ai_gates": {
        "h1_poi_availability_enabled": True,
    },
}


def make_config(overrides: Optional[dict] = None) -> dict:
    """Return DEFAULT_REPLAY_CONFIG deep-merged with ``overrides``."""
    import copy
    cfg = copy.deepcopy(DEFAULT_REPLAY_CONFIG)
    if overrides:
        _deep_merge(cfg, overrides)
    return cfg


def _deep_merge(dst: dict, src: dict) -> None:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v


# ---------------------------------------------------------------------------
# Historical fills (best-effort extraction from trade_records)
# ---------------------------------------------------------------------------


def is_historical_fill(record: dict) -> bool:
    """True if the trade_record represents an actual executed fill.

    A "fill" in the strict sense requires execution metadata with a fill
    timestamp. In April 2026 the trade_records schema captures execution
    as ``record["execution"]`` (may be None for pre-fill snapshots) — we
    treat ``execution`` with a truthy ``filled_at`` or ``order_ticket`` as
    a fill. Non-fills (including LIMIT_PLACED rows that never filled)
    return False.

    Brief note: if execution metadata shape evolves, update this helper
    (not src/). Callers should treat a False return as "skip, not a fill".
    """
    exe = record.get("execution")
    if not isinstance(exe, dict):
        return False
    if exe.get("filled_at"):
        return True
    if exe.get("fill_time"):
        return True
    # A filled ticket with a non-zero position lot is also a fill.
    ticket = exe.get("order_ticket") or exe.get("position_id")
    if ticket:
        return True
    return False


def outcome_of(record: dict) -> Optional[str]:
    """Return canonical exit outcome ('tp_hit'/'sl_hit'/'be_hit'/'force_close'/
    'broker_close') if recorded, else None.

    Schema: ``record["exit"]["exit_type"]`` or ``record["outcome"]["result"]``.
    """
    exit_blk = record.get("exit")
    if isinstance(exit_blk, dict):
        et = exit_blk.get("exit_type")
        if et:
            return et
    out = record.get("outcome")
    if isinstance(out, dict):
        r = out.get("result") or out.get("exit_type")
        if r:
            return r
    return None


def r_multiple_of(record: dict) -> Optional[float]:
    """Return the realized R multiple for a filled record, or None."""
    for blk_key in ("exit", "outcome"):
        blk = record.get(blk_key)
        if isinstance(blk, dict):
            for k in ("r_multiple", "result_r", "realized_r"):
                v = blk.get(k)
                if isinstance(v, (int, float)):
                    return float(v)
    return None
