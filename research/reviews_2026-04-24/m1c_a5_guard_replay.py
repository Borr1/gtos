"""
M1c Replay — A5 (`guard_candidate_inconsistent_pois`)

Branch: worktree-agent-a432468d
Commit: 385055b feat(safety): post-AI validator for POI/entry/SL consistency

Purpose
-------
Automate the guard replay V5 did by hand. For every historical trade record
(and every CANDIDATE row in `live_evaluations` — schema-dependent, see below),
reconstruct the `PrimaryAnalysisOutput` + `MarketStateObject` the live pipeline
would have produced, re-apply `guard_candidate_inconsistent_pois` from the A5
branch, and tally demotions against `decision_pipeline.final_outcome` +
`execution` to distinguish "caught-before-fill" (safe) from "filled-but-would-
have-demoted" (the actual false-positive bucket).

Data sources
------------
1. `knowledge_base/trade_records/<SYMBOL>/*.json` — full trade-level capture
   that includes `mso` (raw dict matching `MarketStateObject`) and `ai_response`
   (matching `PrimaryAnalysisOutput`). This is the PRIMARY source — it contains
   enough data for bit-exact guard replay.
2. `knowledge_base/live_evaluations/<SYMBOL>/*.jsonl` — summary rows per
   evaluation. These do NOT carry MSO or trade_parameters, so this script
   uses them only for cross-reference counts (not for guard replay).

CANDIDATEs evaluated in the guard replay therefore come from trade_records.
This also means every CANDIDATE in the replay universe has `final_outcome` set
by the pipeline (LIMIT_PLACED / REJECTED_L2 / REJECTED_GATE1_SAFETY /
EXECUTION_FAILED / REJECTED_L2_POST_M5 / etc.).

CLI
---
    python research/reviews_2026-04-24/m1c_a5_guard_replay.py

Optional:
    --window-start YYYY-MM-DD   default 2026-03-24 (30-day window ending 04-22)
    --window-end   YYYY-MM-DD   default 2026-04-22 (last complete live day)
    --symbols XAUUSD,USDJPY,…   default all five
    --json-out    path          dump full demotion rows for offline inspection

Outputs
-------
- stdout summary tables (also suitable for pytest capture)
- optional JSON with per-demotion records at --json-out

Read-only. No API calls. No writes to live data.

Usage in pytest
---------------
Import `run_replay(window_start, window_end, symbols)` and assert on the
returned dict. A guard-regression test could assert `demoted_and_filled == 0`
for the 30-day look-back (ship-blocker if non-zero).

Why the A5 worktree
-------------------
The guard function only exists on branch `worktree-agent-a432468d`. This
script prepends that worktree path to `sys.path` BEFORE importing
`src.components.primary_analyzer` so the bit-exact A5 guard runs (not the
main-branch code that doesn't have the guard).

(Production `src.models.*` Pydantic shapes are byte-identical between branches
so it's safe to share; the branch split is only at the analyzer level.)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Optional


# --- Paths -----------------------------------------------------------------

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
A5_WORKTREE = REPO / ".claude" / "worktrees" / "agent-a432468d"
TRADE_RECORDS = REPO / "knowledge_base" / "trade_records"
LIVE_EVALS = REPO / "knowledge_base" / "live_evaluations"

# Prepend A5 worktree so `src.components.primary_analyzer` resolves to the
# guard-bearing copy. Must happen BEFORE the import.
sys.path.insert(0, str(A5_WORKTREE))

# Silence the guard's logger.error() during replay — it fires on every demote.
import logging  # noqa: E402
logging.getLogger("src.components.primary_analyzer").setLevel(logging.CRITICAL)

from src.components.primary_analyzer import (  # noqa: E402
    guard_candidate_inconsistent_pois,
)
from src.models.analysis_models import PrimaryAnalysisOutput  # noqa: E402
from src.models.market_state_models import MarketStateObject  # noqa: E402


SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]

# Reasons bucket (string contains) — rough but deterministic.
REASON_BUCKETS = [
    ("entry_outside_ob", "outside matched OB"),
    ("sl_not_beyond_long", "not below matched OB low"),
    ("sl_not_beyond_short", "not above matched OB high"),
    ("tp1_wrong_long", "<= entry_price for LONG"),
    ("tp1_wrong_short", ">= entry_price for SHORT"),
]


# --- Data classes ----------------------------------------------------------

@dataclass
class DemotionRow:
    timestamp: str
    symbol: str
    kill_zone: Optional[str]
    source_file: str
    poi_price_level: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    direction: str
    matched_ob_bounds: tuple[float, float]
    matched_ob_touches: int
    matched_ob_mitigated: bool
    reason_detail: str
    reason_buckets: list[str]
    final_outcome: Optional[str]
    execution_present: bool
    filled: bool
    fill_price: Optional[float] = None
    ai_poi_explanation: str = ""


@dataclass
class ReplaySummary:
    window_start: str
    window_end: str
    symbols: list[str]
    candidates_total: int = 0
    demoted_total: int = 0
    demoted_and_filled: int = 0  # THE TRUE FP BUCKET (ship-blocker if > 0)
    demoted_and_limit_placed_not_filled: int = 0
    demoted_and_rejected_already: int = 0
    by_symbol: dict[str, dict[str, int]] = field(default_factory=dict)
    by_kz: dict[str, dict[str, int]] = field(default_factory=dict)
    reason_counts: dict[str, int] = field(default_factory=dict)
    reason_bucket_counts: dict[str, int] = field(default_factory=dict)
    final_outcome_breakdown: dict[str, int] = field(default_factory=dict)
    demotions: list[DemotionRow] = field(default_factory=list)


# --- Core ------------------------------------------------------------------

def _iter_trade_records(symbols: list[str]) -> list[Path]:
    out: list[Path] = []
    for sym in symbols:
        d = TRADE_RECORDS / sym
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.json")):
            if p.name.startswith("_"):  # skip _pending_records_index.json
                continue
            out.append(p)
    return out


def _parse_candle_date(rec: dict) -> Optional[date]:
    """Return candle UTC date from metadata.candle_time if parseable."""
    raw = rec.get("metadata", {}).get("candle_time") or rec.get("metadata", {}).get("date")
    if not raw:
        return None
    try:
        if "T" in raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        return date.fromisoformat(raw[:10])
    except Exception:
        return None


def _in_window(d: Optional[date], start: date, end: date) -> bool:
    if d is None:
        return False
    return start <= d <= end


def _bucket_reasons(detail: str) -> list[str]:
    out = []
    for key, phrase in REASON_BUCKETS:
        if phrase in detail:
            out.append(key)
    return out or ["unknown"]


def _extract_reason_detail(reasoning_text: str) -> str:
    """Extract the structured reason appended by the guard."""
    marker = "ai_output_inconsistent_pois: "
    idx = reasoning_text.rfind(marker)
    if idx < 0:
        return reasoning_text[-400:]
    detail = reasoning_text[idx + len(marker):]
    # Trim trailing ']'
    return detail.rstrip("] ").strip()


def _matched_ob(poi: float, entry: float, h1_obs) -> Optional[dict]:
    """Re-run the guard's matching logic so we can log which OB was matched."""
    matching = [ob for ob in h1_obs if ob.low <= poi <= ob.high]
    if not matching:
        return None
    if len(matching) > 1:
        best = min(
            matching,
            key=lambda ob: min(abs(ob.low - entry), abs(ob.high - entry)),
        )
    else:
        best = matching[0]
    return {
        "low": best.low,
        "high": best.high,
        "touches": getattr(best, "touch_count", 0),
        "mitigated": bool(best.mitigated),
    }


def _is_filled(rec: dict) -> tuple[bool, Optional[float]]:
    """Return (filled, fill_price). A trade is 'filled' iff the live pipeline
    recorded an `execution` dict with fill data. LIMIT_PLACED with execution=None
    (pending that expired) is NOT filled.
    """
    ex = rec.get("execution")
    if not isinstance(ex, dict):
        return False, None
    # Multiple execution schemas exist across the history — check a few fields.
    for key in ("fill_price", "filled_price", "price", "entry_fill_price"):
        if key in ex:
            return True, ex[key]
    # Fallback: any non-null execution dict counts as filled unless it's empty
    return bool(ex), None


def replay_one(path: Path) -> tuple[Optional[PrimaryAnalysisOutput], Optional[PrimaryAnalysisOutput],
                                    Optional[MarketStateObject], dict]:
    """Load + replay guard on one trade record. Returns (before, after, mso, raw_rec).
    `before` / `after` are None if the record isn't a replay candidate
    (no AI CANDIDATE, missing MSO, schema error, etc.)."""
    try:
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
    except Exception:
        return None, None, None, {}

    ai = rec.get("ai_response")
    mso_dict = rec.get("mso")
    if not ai or not mso_dict:
        return None, None, None, rec
    if ai.get("decision") != "CANDIDATE":
        return None, None, None, rec
    try:
        mso = MarketStateObject(**mso_dict)
    except Exception:
        return None, None, None, rec
    try:
        before = PrimaryAnalysisOutput(**ai)
    except Exception:
        return None, None, None, rec
    # Deep-copy semantics: model_copy(deep=True) keeps the original unmodified.
    after = guard_candidate_inconsistent_pois(before.model_copy(deep=True), mso)
    return before, after, mso, rec


def run_replay(window_start: date, window_end: date, symbols: list[str]) -> ReplaySummary:
    summary = ReplaySummary(
        window_start=window_start.isoformat(),
        window_end=window_end.isoformat(),
        symbols=list(symbols),
    )
    for sym in symbols:
        summary.by_symbol[sym] = {"candidates": 0, "demoted": 0, "demoted_filled": 0}
    for kz in ("london", "ny", "tokyo"):
        summary.by_kz[kz] = {"candidates": 0, "demoted": 0, "demoted_filled": 0}

    for path in _iter_trade_records(symbols):
        sym = path.parent.name
        before, after, mso, rec = replay_one(path)
        if before is None:
            continue
        d = _parse_candle_date(rec)
        if not _in_window(d, window_start, window_end):
            continue
        kz = rec.get("metadata", {}).get("kill_zone") or "unknown"
        final_outcome = rec.get("decision_pipeline", {}).get("final_outcome")
        summary.candidates_total += 1
        summary.by_symbol.setdefault(sym, {"candidates": 0, "demoted": 0, "demoted_filled": 0})
        summary.by_symbol[sym]["candidates"] += 1
        summary.by_kz.setdefault(kz, {"candidates": 0, "demoted": 0, "demoted_filled": 0})
        summary.by_kz[kz]["candidates"] += 1
        summary.final_outcome_breakdown[final_outcome or "none"] = (
            summary.final_outcome_breakdown.get(final_outcome or "none", 0) + 1
        )
        if after.decision == "CANDIDATE":
            continue
        # Demoted.
        summary.demoted_total += 1
        summary.by_symbol[sym]["demoted"] += 1
        summary.by_kz[kz]["demoted"] += 1

        # Parse detail + buckets.
        detail = _extract_reason_detail(after.reasoning.overall_reasoning or "")
        buckets = _bucket_reasons(detail)
        for b in buckets:
            summary.reason_bucket_counts[b] = summary.reason_bucket_counts.get(b, 0) + 1
        summary.reason_counts[detail[:220]] = summary.reason_counts.get(detail[:220], 0) + 1

        tp = before.trade_parameters
        matched = _matched_ob(
            before.reasoning.h1_setup.poi_price_level,
            tp.entry_price,
            mso.timeframes["H1"].order_blocks,
        ) if tp else None
        filled, fill_price = _is_filled(rec)
        execution_present = rec.get("execution") is not None
        if filled:
            summary.demoted_and_filled += 1
            summary.by_symbol[sym]["demoted_filled"] += 1
            summary.by_kz[kz]["demoted_filled"] += 1
        elif final_outcome == "LIMIT_PLACED":
            summary.demoted_and_limit_placed_not_filled += 1
        else:
            summary.demoted_and_rejected_already += 1

        summary.demotions.append(DemotionRow(
            timestamp=rec.get("metadata", {}).get("candle_time", ""),
            symbol=sym,
            kill_zone=kz,
            source_file=str(path.relative_to(REPO)),
            poi_price_level=before.reasoning.h1_setup.poi_price_level,
            entry_price=tp.entry_price if tp else 0.0,
            stop_loss=tp.stop_loss if tp else 0.0,
            take_profit_1=tp.take_profit_1 if tp else 0.0,
            direction=tp.direction if tp else "?",
            matched_ob_bounds=(matched["low"], matched["high"]) if matched else (0.0, 0.0),
            matched_ob_touches=matched["touches"] if matched else -1,
            matched_ob_mitigated=matched["mitigated"] if matched else False,
            reason_detail=detail,
            reason_buckets=buckets,
            final_outcome=final_outcome,
            execution_present=execution_present,
            filled=filled,
            fill_price=fill_price,
            ai_poi_explanation=before.reasoning.h1_setup.explanation,
        ))
    return summary


# --- V5 cross-check --------------------------------------------------------

def v5_cross_check() -> dict:
    """Assert V5's single-FP finding: USDJPY 2026-04-22 ny_1515."""
    path = TRADE_RECORDS / "USDJPY" / "2026-04-22_ny_1515.json"
    if not path.exists():
        return {"ok": False, "reason": f"target file missing: {path}"}
    before, after, mso, rec = replay_one(path)
    if before is None:
        return {"ok": False, "reason": "replay_one returned None (schema mismatch?)"}
    if after.decision != "NO_TRADE":
        return {"ok": False, "reason": f"expected NO_TRADE, got {after.decision}"}
    if after.no_trade_reason != "ai_output_inconsistent_pois":
        return {"ok": False, "reason": f"expected ai_output_inconsistent_pois, got {after.no_trade_reason}"}
    tp = before.trade_parameters
    matched = _matched_ob(
        before.reasoning.h1_setup.poi_price_level,
        tp.entry_price,
        mso.timeframes["H1"].order_blocks,
    )
    filled, fill_price = _is_filled(rec)
    return {
        "ok": True,
        "demoted": after.decision == "NO_TRADE",
        "reason": after.no_trade_reason,
        "poi": before.reasoning.h1_setup.poi_price_level,
        "entry": tp.entry_price,
        "stop_loss": tp.stop_loss,
        "matched_ob": (matched["low"], matched["high"]) if matched else None,
        "matched_ob_touches": matched["touches"] if matched else None,
        "final_outcome": rec.get("decision_pipeline", {}).get("final_outcome"),
        "execution_present": rec.get("execution") is not None,
        "filled": filled,
    }


# --- Output formatting -----------------------------------------------------

def fmt_table(rows: list[tuple], headers: tuple) -> str:
    widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    def fmt_row(vals):
        return " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(vals))
    sep = "-+-".join("-" * w for w in widths)
    return "\n".join([fmt_row(headers), sep] + [fmt_row(r) for r in rows])


def print_summary(s: ReplaySummary) -> None:
    print(f"\n=== Replay window: {s.window_start} to {s.window_end} ===")
    print(f"Symbols: {','.join(s.symbols)}")
    print(f"CANDIDATEs evaluated: {s.candidates_total}")
    print(f"Demoted total:        {s.demoted_total}")
    print(f"  Demoted & FILLED (true FP):          {s.demoted_and_filled}")
    print(f"  Demoted & LIMIT_PLACED (never filled): {s.demoted_and_limit_placed_not_filled}")
    print(f"  Demoted & already rejected elsewhere:  {s.demoted_and_rejected_already}")

    print("\nBy symbol:")
    rows = [(sym, d["candidates"], d["demoted"], d["demoted_filled"]) for sym, d in s.by_symbol.items()]
    print(fmt_table(rows, ("symbol", "cands", "demoted", "demoted_filled")))

    print("\nBy kill zone:")
    rows = [(kz, d["candidates"], d["demoted"], d["demoted_filled"]) for kz, d in s.by_kz.items()]
    print(fmt_table(rows, ("kz", "cands", "demoted", "demoted_filled")))

    print("\nDemotion reason buckets:")
    rows = sorted(s.reason_bucket_counts.items(), key=lambda x: -x[1])
    print(fmt_table(rows, ("bucket", "count")))

    print("\nFinal-outcome distribution of evaluated CANDs:")
    rows = sorted(s.final_outcome_breakdown.items(), key=lambda x: -x[1])
    print(fmt_table(rows, ("final_outcome", "count")))

    if s.demoted_and_filled > 0:
        print("\n*** SHIP-BLOCKER ***")
        for dr in s.demotions:
            if dr.filled:
                print(f"  FP: {dr.timestamp} {dr.symbol} {dr.kill_zone}")
                print(f"       {dr.reason_detail}")
                print(f"       fill_price={dr.fill_price}")


def verdict(s: ReplaySummary) -> str:
    if s.demoted_and_filled > 0:
        return "CONCERNS FOUND - at least one FILLED trade would have been demoted"
    return "SAFE TO SHIP - zero filled trades would have been demoted in window"


# --- CLI -------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="A5 guard replay across historical trade records.")
    ap.add_argument("--window-start", default="2026-03-24")
    ap.add_argument("--window-end", default="2026-04-22")
    ap.add_argument("--symbols", default=",".join(SYMBOLS))
    ap.add_argument("--json-out", default=None, help="Optional path to dump demotion rows as JSON.")
    ap.add_argument("--whole-history", action="store_true",
                    help="Ignore date window; replay entire trade_records archive.")
    args = ap.parse_args()

    start = date.fromisoformat(args.window_start)
    end = date.fromisoformat(args.window_end)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    # V5 cross-check.
    print("=== V5 cross-check (USDJPY 2026-04-22 ny_1515) ===")
    chk = v5_cross_check()
    for k, v in chk.items():
        print(f"  {k}: {v}")
    if chk.get("ok"):
        print("V5 finding REPRODUCED.")
    else:
        print("V5 finding DID NOT REPRODUCE — investigate.")

    if args.whole_history:
        start = date(1970, 1, 1)
        end = date(2999, 1, 1)

    s = run_replay(start, end, symbols)
    print_summary(s)
    print(f"\nVerdict: {verdict(s)}")

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "window_start": s.window_start,
            "window_end": s.window_end,
            "symbols": s.symbols,
            "summary": {
                "candidates_total": s.candidates_total,
                "demoted_total": s.demoted_total,
                "demoted_and_filled": s.demoted_and_filled,
                "demoted_and_limit_placed_not_filled": s.demoted_and_limit_placed_not_filled,
                "demoted_and_rejected_already": s.demoted_and_rejected_already,
            },
            "by_symbol": s.by_symbol,
            "by_kz": s.by_kz,
            "reason_bucket_counts": s.reason_bucket_counts,
            "final_outcome_breakdown": s.final_outcome_breakdown,
            "v5_cross_check": chk,
            "demotions": [asdict(dr) for dr in s.demotions],
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"\nWrote JSON: {out_path}")

    return 0 if s.demoted_and_filled == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
