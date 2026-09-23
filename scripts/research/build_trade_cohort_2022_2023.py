"""Build mechanical OB-retest trade cohort for 2022-01-01 -> 2024-02-20 OHLCV.

Mirrors the F11 mechanical population schema (research/edge_decomposition/
F11_ob_zone_original_geometry/population.jsonl) which K54's
scripts/k54_build_features.py:_row_from_f11 (in
.claude/worktrees/agent-a01c00db65592ac2b/scripts/k54_build_features.py:221-293)
expects:

    {
      "bos": {symbol, bos_time, bos_index, direction, swing_level_broken,
              swing_time, anchor_swing_price, anchor_swing_time, anchor_swing_index,
              bos_close, bos_high, bos_low, atr_at_bos,
              ob_high, ob_low, ob_index, ob_time, ob_skip_reason},
      "ob_retest": {bos_id, strategy, skip_reason, entry, sl, tp, rr,
                    outcome, realized_r, bars_in_trade, exit_time}
    }

Re-uses the production research_infra modules:
  src/research_infra/ob_zone_test.py: extract_bos_events, find_ob_retest_outcome
  src/research_infra/dumb_baseline.py: resolve_mechanical_outcome (M15 walk)

OHLCV dir = data/historical_2022_2023/  (set via m15_ohlcv_dir parameter to the resolver).

For each (instrument, BOS event) pair:
  1. Extract BOS via extract_bos_events on H1 CSV.
  2. Resolve mechanical OB retest outcome via find_ob_retest_outcome on M15 CSV.
  3. Emit one JSONL row to data/historical_2022_2023/trade_cohort.jsonl.

Also emits trade_cohort.csv with the columns _row_from_f11 produces
(unified K54 schema) so downstream Q1.4 ML work can consume directly.

Phase 1 = $0 API. NO Anthropic / OpenRouter calls.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Import production research infra (read-only; we don't mutate it).
from src.research_infra.ob_zone_test import (  # noqa: E402
    BOSEvent,
    Outcome,
    extract_bos_events,
    find_ob_retest_outcome,
)


OHLCV_DIR = PROJECT_ROOT / "data" / "historical_2022_2023"
OUT_JSONL = OHLCV_DIR / "trade_cohort.jsonl"
OUT_CSV = OHLCV_DIR / "trade_cohort.csv"

INSTRUMENTS = ("XAUUSD", "XAGUSD", "USDJPY", "GBPUSD", "NAS100")
START = dt.datetime(2022, 1, 1, tzinfo=dt.timezone.utc)
END = dt.datetime(2024, 2, 20, tzinfo=dt.timezone.utc)


# Mirror of dataclass-asdict serialization from F11
def _serialize_bos(bos: BOSEvent) -> dict:
    d = asdict(bos)
    for k in ("bos_time", "swing_time", "anchor_swing_time", "ob_time"):
        v = d.get(k)
        if isinstance(v, dt.datetime):
            d[k] = v.isoformat()
    return d


def _serialize_outcome(o: Outcome) -> dict:
    return asdict(o)


# K54 v1 unified schema (exact column order from k54_build_features.py:478-488)
K54_FIELDNAMES = [
    "trade_id", "source", "date_iso", "symbol", "instrument_class",
    "direction_long_short", "kill_zone", "hour_utc", "day_of_week",
    "framework", "setup_grade",
    "regime_tag", "counter_direction_flag",
    "ob_distance_atr", "ob_age_candles", "displacement_quality_score",
    "fvg_present", "touch_count",
    "ai_confidence", "walk_level_signal",
    "cross_instrument_xau_dir",
    "realized_r", "win_label",
]

INSTRUMENT_CLASS_MAP = {
    "XAUUSD": "metals",
    "XAGUSD": "metals",
    "USDJPY": "fx",
    "GBPUSD": "fx",
    "NAS100": "indices",
}


def _kill_zone_from_hour(h: int) -> str:
    if 7 <= h < 12:
        return "london"
    if 13 <= h < 17:
        return "ny"
    if 0 <= h < 4:
        return "tokyo"
    return "other"


def _load_regime_index(path: Path) -> dict[tuple[str, str], dict]:
    """Index regime backfill rows by (symbol_upper, h4_iso_hour)."""
    out: dict[tuple[str, str], dict] = {}
    if not path.exists():
        return out
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        sym = str(d.get("symbol", "")).upper()
        ts_raw = d.get("ts")
        if not sym or not ts_raw:
            continue
        try:
            ts = dt.datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        except Exception:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        h4_hour = (ts.hour // 4) * 4
        key = (sym, ts.replace(hour=h4_hour, minute=0, second=0, microsecond=0).isoformat())
        out[key] = {
            "regime": d.get("v2_direction") or d.get("production_label"),
            "score": d.get("v2_score"),
            "dead_zone": d.get("v2_dead_zone"),
        }
    return out


def _regime_lookup(idx: dict, sym: str, ts: dt.datetime | None) -> dict:
    if ts is None or not idx:
        return {"regime": None, "score": None, "dead_zone": None}
    sym_u = str(sym).upper()
    for hours_back in (0, 4, 8, 12):
        probe = ts - dt.timedelta(hours=hours_back)
        h4_hour = (probe.hour // 4) * 4
        key = (sym_u, probe.replace(hour=h4_hour, minute=0, second=0, microsecond=0).isoformat())
        if key in idx:
            return idx[key]
    return {"regime": None, "score": None, "dead_zone": None}


def _bos_to_k54_row(bos: BOSEvent, ob: Outcome, regime_idx: dict) -> dict:
    """Transform a (BOS + OB-retest outcome) pair into the K54 unified row.

    Mirrors scripts/k54_build_features.py:_row_from_f11 (lines 221-293) so
    downstream tools see an identical schema.
    """
    sym = str(bos.symbol).upper()
    direction = bos.direction
    bos_time = bos.bos_time
    ob_time = bos.ob_time

    ob_age = None
    if bos_time and ob_time:
        ob_age = max(0, int((bos_time - ob_time).total_seconds() // (15 * 60)))

    entry = ob.entry
    atr = bos.atr_at_bos
    ob_top = bos.ob_high
    ob_bot = bos.ob_low
    ob_distance_atr = None
    if entry is not None and atr and ob_top is not None and ob_bot is not None:
        try:
            mid = (float(ob_top) + float(ob_bot)) / 2.0
            ob_distance_atr = (float(entry) - mid) / float(atr)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    hour_utc = bos_time.hour if bos_time else -1
    kz = _kill_zone_from_hour(hour_utc) if hour_utc != -1 else "other"
    dow = bos_time.weekday() if bos_time else -1

    regime = _regime_lookup(regime_idx, sym, bos_time)
    counter_dir = 0
    if regime.get("regime"):
        r = regime["regime"]
        if (r == "bullish" and direction == "SHORT") or (r == "bearish" and direction == "LONG"):
            counter_dir = 1

    realized = ob.realized_r
    return {
        "trade_id": ob.bos_id or f"{sym}|{bos_time.isoformat()}|f11",
        "source": "f11_mechanical",
        "date_iso": bos_time.isoformat() if bos_time else "",
        "symbol": sym,
        "instrument_class": INSTRUMENT_CLASS_MAP.get(sym, "other"),
        "direction_long_short": direction,
        "kill_zone": kz,
        "hour_utc": hour_utc,
        "day_of_week": dow,
        "framework": "ob_retest",
        "setup_grade": "",
        "regime_tag": regime.get("regime") or "",
        "counter_direction_flag": counter_dir,
        "ob_distance_atr": ob_distance_atr if ob_distance_atr is not None else 0.0,
        "ob_age_candles": ob_age if ob_age is not None else 0,
        "displacement_quality_score": 0.5,
        "fvg_present": 0,
        "touch_count": 0,
        "ai_confidence": -1,
        "walk_level_signal": -1,
        "cross_instrument_xau_dir": "",
        "realized_r": float(realized) if realized is not None else "",
        "win_label": 1 if (realized is not None and float(realized) > 0) else 0,
    }


def main() -> int:
    regime_path = PROJECT_ROOT / "shadow_logs" / "structure_detector_backfill_2022_2023.jsonl"
    print(f"Loading regime backfill: {regime_path}")
    regime_idx = _load_regime_index(regime_path)
    print(f"  regime rows indexed: {len(regime_idx)}")
    print()

    rows_jsonl: list[dict] = []
    rows_csv: list[dict] = []

    summary = {}
    for sym in INSTRUMENTS:
        h1_path = OHLCV_DIR / f"{sym}_H1.csv"
        if not h1_path.exists():
            print(f"{sym}: H1 CSV missing, SKIP")
            summary[sym] = {"bos": 0, "filled": 0, "errors": "h1_missing"}
            continue
        print(f"=== {sym} ===")
        bos_events = extract_bos_events(h1_path, symbol=sym, start=START, end=END)
        print(f"  BOS events extracted: {len(bos_events)}")

        filled = 0
        no_entry = 0
        skipped = 0
        for bos in bos_events:
            # Resolve OB-retest outcome on M15 in OHLCV_DIR
            ob_out = find_ob_retest_outcome(bos, h1_path, m15_ohlcv_dir=OHLCV_DIR)
            rows_jsonl.append({
                "bos": _serialize_bos(bos),
                "ob_retest": _serialize_outcome(ob_out),
            })
            if ob_out.outcome in ("TP", "SL", "TIMEOUT"):
                filled += 1
                rows_csv.append(_bos_to_k54_row(bos, ob_out, regime_idx))
            elif ob_out.outcome == "NO_ENTRY":
                no_entry += 1
            else:
                skipped += 1
        print(f"  Resolved: filled={filled}, no_entry={no_entry}, skipped={skipped}")
        summary[sym] = {"bos": len(bos_events), "filled": filled, "no_entry": no_entry, "skipped": skipped}
        print()

    # Write JSONL (one per BOS, includes NO_ENTRY rows for compat with F11 pop schema)
    OHLCV_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("w", encoding="utf-8") as fh:
        for r in rows_jsonl:
            fh.write(json.dumps(r) + "\n")

    # Write CSV with K54 unified schema (filled-only; matches realized_r != None)
    rows_csv.sort(key=lambda r: (r["date_iso"], r["symbol"], r["trade_id"]))
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=K54_FIELDNAMES, lineterminator="\n")
        w.writeheader()
        w.writerows(rows_csv)

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"JSONL: {OUT_JSONL}  ({len(rows_jsonl)} rows)")
    print(f"CSV  : {OUT_CSV}    ({len(rows_csv)} filled rows)")
    for sym, s in summary.items():
        print(f"  {sym}: BOS={s.get('bos',0)}, filled={s.get('filled',0)}, "
              f"no_entry={s.get('no_entry',0)}, skipped={s.get('skipped',0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
