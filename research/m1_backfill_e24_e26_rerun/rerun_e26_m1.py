"""P1 Phase B — Re-run E24+E26 microstructure correlation with REAL M1.

This driver mirrors the original ``research/e24_e26_microstructure/run_e26.py``
driver (in worktree ``agent-aa2fb2a929295aed4``, branch
``feat/research-e24-e26-microstructure``, commit ``50df95a``) but:

* Uses the ``M1.csv`` files written by ``backfill_m1.py`` (canonical
  ``data/historical_2026/{SYMBOL}_M1.csv``), so the synthetic-tick
  reconstructor receives real 1-minute OHLCV instead of M15-bar
  fallback.
* Removes the ``allow_m15_fallback=True`` switch so any symbol missing
  M1 explicitly errors (no silent degradation).
* Filters fills to the date range covered by the M1 CSV (broker M1 cap
  starts ~2026-01-14 to 2026-01-20 depending on symbol). Fills outside
  the M1 window are tagged ``OUT_OF_M1_RANGE`` and excluded.
* Writes a comparison-friendly artifact bundle:
    - ``per_fill_features_m1.csv``
    - ``feature_correlations_m1.csv``
    - ``per_feature_comparison.csv`` — side-by-side M15-fallback vs M1
    - ``results.json``
    - ``report.md``

Hard rules carried forward from the original module
===================================================
* Bonferroni across (instrument × feature) family.
* n >= 10 minimum per cell (INSUFFICIENT_N flag below that).
* Realized R is the verdict, not walk-level counts.
* Pure-Python statistics (no scipy).
"""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Repo root on sys.path so we can import src.research_infra.*
ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
sys.path.insert(0, str(ROOT))

from src.research_infra.microstructure_features import (
    DEFAULT_LOOKBACK_MIN,
    FEATURE_NAMES,
    aggregate_by_feature,
    compute_features_for_fill,
    correlate_features_with_r,
)
from src.research_infra.synthetic_tick_reconstructor import (
    bar_lee_ready_direction,
    emit_sample_csv,
    load_sub_m15_bars,
    reconstruct_ticks_for_bar,
)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("rerun_e26_m1")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SESSIONS_DIR = ROOT / "knowledge_base_backtest" / "sessions"
DATA_DIR = ROOT / "data" / "historical_2026"
OUT_DIR = Path(__file__).resolve().parent

# Prior M15-fallback baseline results (from worktree commit 50df95a)
PRIOR_RESULTS = ROOT / ".claude" / "worktrees" / "agent-aa2fb2a929295aed4" / "research" / "e24_e26_microstructure" / "results.json"

# All 7 production instruments. Note XAGUSD/NAS100 have NO backtest sessions
# directory (per project state) — they will be tagged NO_FILLS.
SYMBOLS = ["XAUUSD", "GBPJPY", "GBPUSD", "USDJPY", "US30_cash", "XAGUSD", "NAS100", "NZDUSD"]
LOOKBACK_MIN = DEFAULT_LOOKBACK_MIN  # 60 minutes


# ---------------------------------------------------------------------------
# Step 1 — harvest fills from backtest sessions (same as prior driver)
# ---------------------------------------------------------------------------


def harvest_fills() -> list[dict]:
    """Walk knowledge_base_backtest/sessions/ and pull every confirmed fill."""
    fills: list[dict] = []
    for sym in SYMBOLS:
        sym_dir = SESSIONS_DIR / sym
        if not sym_dir.is_dir():
            logger.info("No session subdir for %s: %s", sym, sym_dir)
            continue
        for fname in sorted(os.listdir(sym_dir)):
            if not fname.endswith(".json"):
                continue
            fp = sym_dir / fname
            try:
                with open(fp) as fh:
                    d = json.load(fh)
            except Exception as e:
                logger.warning("Failed to read %s: %s", fp, e)
                continue
            ts = d.get("trade_summary", {})
            if not ts.get("trade_taken"):
                continue
            for t in ts.get("trades", []):
                ct = None
                fw = None
                grade = None
                for ce in d.get("candle_evaluations", []):
                    if ce.get("trade_executed") is True:
                        ct = ce.get("candle_time")
                        fw = ce.get("framework")
                        grade = ce.get("setup_grade")
                        break
                if not ct or t.get("r_multiple") is None:
                    continue
                ct_str = ct
                if ct_str.endswith("Z"):
                    ct_str = ct_str[:-1] + "+00:00"
                ct_dt = datetime.fromisoformat(ct_str)
                if ct_dt.tzinfo is None:
                    ct_dt = ct_dt.replace(tzinfo=timezone.utc)
                candle_close = ct_dt + timedelta(minutes=15)
                fills.append({
                    "fill_id": t.get("trade_id"),
                    "symbol": sym,
                    "date": d.get("date"),
                    "candle_open_ts": ct_dt,
                    "candle_close_ts": candle_close,
                    "kill_zone": t.get("kill_zone"),
                    "framework": fw,
                    "setup_grade": grade,
                    "r_multiple": float(t.get("r_multiple")),
                    "outcome": t.get("outcome"),
                    "mfe_r": t.get("mfe_r"),
                    "mae_r": t.get("mae_r"),
                })
    return fills


# ---------------------------------------------------------------------------
# Step 2 — per-symbol feature extraction with REAL M1 only
# ---------------------------------------------------------------------------


def extract_features_real_m1(fills: list[dict]) -> tuple[list[dict], dict]:
    """Group by symbol, load M1 OHLC once per symbol, extract per-fill features.

    No fallback to M5 or M15 — symbols missing M1 are reported in telemetry
    rather than silently degraded.
    """
    by_sym: dict[str, list[dict]] = {}
    for f in fills:
        by_sym.setdefault(f["symbol"], []).append(f)

    out: list[dict] = []
    timeframes: dict[str, str] = {}
    skipped_by_sym: Counter = Counter()
    skip_reasons: Counter = Counter()
    skipped_total = 0

    for sym, sym_fills in by_sym.items():
        # Hard requirement: M1 file must exist
        m1_path = DATA_DIR / f"{sym}_M1.csv"
        if not m1_path.exists():
            logger.warning("Skipping %s: M1 file missing %s", sym, m1_path)
            skipped_by_sym[sym] += len(sym_fills)
            skip_reasons["M1_FILE_MISSING"] += len(sym_fills)
            skipped_total += len(sym_fills)
            continue

        # Use load_sub_m15_bars without fallback to force M1
        try:
            bars, tf = load_sub_m15_bars(sym, DATA_DIR, allow_m15_fallback=False)
        except FileNotFoundError as e:
            logger.warning("Skipping %s: %s", sym, e)
            skipped_by_sym[sym] += len(sym_fills)
            skip_reasons["M1_LOAD_ERROR"] += len(sym_fills)
            skipped_total += len(sym_fills)
            continue

        if tf != "M1":
            # Defensive — should always be M1 when allow_m15_fallback=False and
            # M5 isn't shipped, but assert just in case the loader picks something else.
            logger.warning("Symbol %s loader returned tf=%s, expected M1; skipping", sym, tf)
            skipped_by_sym[sym] += len(sym_fills)
            skip_reasons["UNEXPECTED_TF"] += len(sym_fills)
            skipped_total += len(sym_fills)
            continue

        timeframes[sym] = tf
        first = bars[0]["time"]
        last = bars[-1]["time"]
        for fill in sym_fills:
            # Need a full lookback window of bars: [close - lookback, close)
            window_start = fill["candle_close_ts"] - timedelta(minutes=LOOKBACK_MIN)
            if fill["candle_close_ts"] < first or fill["candle_close_ts"] > last:
                skipped_by_sym[sym] += 1
                skip_reasons["OUT_OF_M1_RANGE"] += 1
                skipped_total += 1
                continue
            if window_start < first:
                # Lookback would extend before the M1 floor; partial window biases
                # cumulative_delta. Skip rather than tolerate.
                skipped_by_sym[sym] += 1
                skip_reasons["LOOKBACK_PARTIAL"] += 1
                skipped_total += 1
                continue
            feats = compute_features_for_fill(fill, bars, lookback_min=LOOKBACK_MIN)
            if feats is None:
                skipped_by_sym[sym] += 1
                skip_reasons["NO_BARS_IN_WINDOW"] += 1
                skipped_total += 1
                continue
            feats["input_timeframe"] = tf
            feats["fill_id"] = fill["fill_id"]
            feats["framework"] = fill["framework"]
            feats["setup_grade"] = fill["setup_grade"]
            feats["kill_zone"] = fill["kill_zone"]
            feats["outcome"] = fill["outcome"]
            out.append(feats)

    return out, {
        "loaded_symbols": list(timeframes.keys()),
        "input_timeframes": timeframes,
        "skipped_fills": skipped_total,
        "skipped_by_symbol": dict(skipped_by_sym),
        "skip_reasons": dict(skip_reasons),
        "total_fills_in": len(fills),
        "total_features_out": len(out),
    }


# ---------------------------------------------------------------------------
# Step 3 — sample reconstructor validation (now from real M1)
# ---------------------------------------------------------------------------


def write_reconstructor_validation_sample() -> dict:
    """Pick one fill window and dump the 4-tick OHLC path for sanity-checking.

    Uses real M1, NOT M15 fallback.
    """
    sample_path = OUT_DIR / "reconstructor_validation_m1.csv"
    summary = emit_sample_csv(
        "XAUUSD",
        DATA_DIR,
        sample_path,
        window_start=datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc),
        window_end=datetime(2026, 4, 15, 13, 30, tzinfo=timezone.utc),
        allow_m15_fallback=False,
    )
    return summary


# ---------------------------------------------------------------------------
# Step 4 — build comparison vs M15-fallback baseline
# ---------------------------------------------------------------------------


def load_prior_baseline() -> dict[tuple[str, str], dict]:
    """Load the M15-fallback baseline correlations into a dict keyed by (sym, feat)."""
    if not PRIOR_RESULTS.exists():
        logger.warning("Prior baseline %s not found; comparison column will be blank", PRIOR_RESULTS)
        return {}
    with open(PRIOR_RESULTS) as fh:
        d = json.load(fh)
    return {(r["symbol"], r["feature"]): r for r in d.get("per_cell_correlations", [])}


def build_comparison(cell_rows: list[dict], prior: dict) -> list[dict]:
    """Side-by-side per-cell comparison: M15-fallback vs M1."""
    rows = []
    for r in cell_rows:
        prior_r = prior.get((r["symbol"], r["feature"]))
        rows.append({
            "symbol": r["symbol"],
            "feature": r["feature"],
            "n_m1": r.get("n"),
            "rho_m1": r.get("spearman_rho"),
            "p_m1": r.get("p_value"),
            "p_bf_m1": r.get("p_bonferroni"),
            "verdict_m1": r.get("verdict"),
            "n_m15": prior_r.get("n") if prior_r else None,
            "rho_m15": prior_r.get("spearman_rho") if prior_r else None,
            "p_m15": prior_r.get("p_value") if prior_r else None,
            "p_bf_m15": prior_r.get("p_bonferroni") if prior_r else None,
            "verdict_m15": prior_r.get("verdict") if prior_r else None,
            "delta_rho_abs": (
                round(abs((r.get("spearman_rho") or 0.0)) - abs((prior_r.get("spearman_rho") or 0.0)), 4)
                if prior_r and r.get("spearman_rho") is not None and prior_r.get("spearman_rho") is not None
                else None
            ),
        })
    return rows


# ---------------------------------------------------------------------------
# Step 5 — verdict logic + report
# ---------------------------------------------------------------------------


def determine_global_verdict(cell_rows: list[dict]) -> tuple[str, str]:
    """Return (verdict_code, narrative)."""
    survivors = [r for r in cell_rows if r.get("verdict") == "SURVIVES_BONFERRONI"]
    raw_sigs = [r for r in cell_rows if r.get("verdict") == "RAW_SIG_NOT_SURVIVING"]
    if survivors:
        return ("MICROSTRUCTURE_SIGNAL_FOUND",
                f"{len(survivors)} (symbol × feature) cell(s) survived Bonferroni at alpha=0.05.")
    if raw_sigs:
        return ("WEAK_RAW_SIGNAL_NO_SURVIVOR",
                f"{len(raw_sigs)} cell(s) raw-significant but none survived Bonferroni.")
    return ("NULL_VERDICT_CONFIRMED",
            "No (symbol × feature) cell reached raw significance even with real M1. "
            "The M15-fallback null verdict from the prior E24+E26 run is upheld.")


def write_report(
    cell_rows: list[dict],
    pooled: list[dict],
    comparison: list[dict],
    telemetry: dict,
    sample_summary: dict,
    verdict: tuple[str, str],
    backfill_log_path: Path,
) -> Path:
    rp = OUT_DIR / "report.md"
    survivors = [r for r in cell_rows if r.get("verdict") == "SURVIVES_BONFERRONI"]
    raw_sigs = [r for r in cell_rows if r.get("verdict") == "RAW_SIG_NOT_SURVIVING"]
    no_signal = [r for r in cell_rows if r.get("verdict") == "NO_SIGNAL"]
    insufficient = [r for r in cell_rows if r.get("verdict") == "INSUFFICIENT_N"]

    # Per-symbol effective n (from per_fill features count)
    by_sym_count: Counter = Counter()
    for c in cell_rows:
        by_sym_count[c["symbol"]] = max(by_sym_count[c["symbol"]], c.get("n") or 0)

    lines = []
    lines.append("# P1 — M1 backfill + E24/E26 re-run (real M1)")
    lines.append("")
    lines.append(f"_Generated_: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"_Branch_: feat/research-m1-backfill-microstructure-rerun")
    lines.append("")
    lines.append("## Executive verdict")
    lines.append("")
    lines.append(f"**Verdict code: `{verdict[0]}`**")
    lines.append("")
    lines.append(verdict[1])
    lines.append("")
    lines.append("## Phase A — M1 backfill (redacted_account-Server 2)")
    lines.append("")
    lines.append("- All 7 production instruments backfilled from MT5 as of "
                 f"{datetime.now(timezone.utc).date().isoformat()}.")
    lines.append("- **Broker M1 cap empirically observed**: oldest available M1 ranges from "
                 "2026-01-14 (XAUUSD/US30/XAGUSD/NAS100) to 2026-01-20 (FX pairs).")
    lines.append("- All symbols pulled the maximum 100,003 M1 bars (~3.5 months). "
                 "redacted_account-Server 2 does NOT serve M1 history beyond ~2026-01-14, so "
                 "the broker cap is below the 1-year minimum mentioned in the task brief.")
    lines.append("")
    lines.append("Per-symbol details: see "
                 f"`research/m1_backfill_e24_e26_rerun/{backfill_log_path.name}`.")
    lines.append("")
    lines.append("## Phase B — E24/E26 re-run with real M1")
    lines.append("")
    lines.append("### Telemetry")
    lines.append("")
    lines.append(f"- Total backtest fills harvested: {telemetry['total_fills_in']}")
    lines.append(f"- Per-fill feature rows out: {telemetry['total_features_out']}")
    lines.append(f"- Skipped: {telemetry['skipped_fills']} "
                 f"(reasons: {telemetry['skip_reasons']})")
    lines.append(f"- Symbols with M1 loaded: {telemetry['loaded_symbols']}")
    lines.append("")
    lines.append("### Per-cell correlations (real M1)")
    lines.append("")
    lines.append("| symbol | feature | n | rho | p | p_bonferroni | verdict |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in cell_rows:
        lines.append(
            f"| {r['symbol']} | {r['feature']} | {r['n']} "
            f"| {r['spearman_rho']} | {r['p_value']} | {r['p_bonferroni']} "
            f"| {r['verdict']} |"
        )
    lines.append("")
    lines.append(f"**Family size (cells with n >= 10)**: "
                 f"{len(cell_rows) - len(insufficient)}")
    lines.append(f"- SURVIVES_BONFERRONI: {len(survivors)}")
    lines.append(f"- RAW_SIG_NOT_SURVIVING: {len(raw_sigs)}")
    lines.append(f"- NO_SIGNAL: {len(no_signal)}")
    lines.append(f"- INSUFFICIENT_N: {len(insufficient)}")
    lines.append("")
    lines.append("### Per-feature pooled view")
    lines.append("")
    lines.append("| feature | cells | median rho | mean rho | raw_sig | bonferroni | verdict |")
    lines.append("|---|---|---|---|---|---|---|")
    for p in pooled:
        lines.append(
            f"| {p['feature']} | {p['cells_tested']} | {p['median_spearman']} "
            f"| {p.get('mean_spearman')} | {p['raw_sig_count']} "
            f"| {p['bonferroni_survivors']} | {p['verdict']} |"
        )
    lines.append("")
    lines.append("### Side-by-side: M15-fallback baseline vs real-M1 re-run")
    lines.append("")
    lines.append("This is the load-bearing comparison: did real M1 surface signal that "
                 "the M15-fallback proxy missed?")
    lines.append("")
    lines.append("| symbol | feature | n_m1 | rho_m1 | p_bf_m1 | n_m15 | rho_m15 | p_bf_m15 | delta_|rho| | verdict_m1 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for c in comparison:
        lines.append(
            f"| {c['symbol']} | {c['feature']} | {c['n_m1']} | {c['rho_m1']} "
            f"| {c['p_bf_m1']} | {c['n_m15']} | {c['rho_m15']} | {c['p_bf_m15']} "
            f"| {c['delta_rho_abs']} | {c['verdict_m1']} |"
        )
    lines.append("")
    lines.append("### Top-3 absolute rho per cell (M1)")
    sorted_cells = sorted(
        [r for r in cell_rows if r.get("spearman_rho") is not None],
        key=lambda r: abs(r["spearman_rho"]),
        reverse=True,
    )[:3]
    lines.append("")
    lines.append("| symbol | feature | rho | p | p_bf | n |")
    lines.append("|---|---|---|---|---|---|")
    for r in sorted_cells:
        lines.append(
            f"| {r['symbol']} | {r['feature']} | {r['spearman_rho']} "
            f"| {r['p_value']} | {r['p_bonferroni']} | {r['n']} |"
        )
    lines.append("")
    lines.append("## Phase 2 implication")
    lines.append("")
    if verdict[0] == "MICROSTRUCTURE_SIGNAL_FOUND":
        # Identify which features survived
        feats = sorted({r["feature"] for r in cell_rows if r["verdict"] == "SURVIVES_BONFERRONI"})
        lines.append("**At least one synthetic-tick microstructure feature recovered "
                     "non-null signal under real M1 input.**")
        lines.append("")
        lines.append(f"- Feature(s) with surviving cells: `{', '.join(feats)}`")
        lines.append("- Recommendation: design Phase 2 prompt enhancement to include the "
                     "winning feature(s) in MSO payload as observation-only first; gate "
                     "promotion on (a) shadow correlation holding ≥30 days live, "
                     "(b) realized-R impact ≥+0.1R per CANDIDATE.")
    elif verdict[0] == "WEAK_RAW_SIGNAL_NO_SURVIVOR":
        lines.append("**Real M1 surfaced raw-significant cells but none survived Bonferroni.**")
        lines.append("")
        lines.append("This is suggestive but not promotion-grade. Recommendation: do NOT add "
                     "any feature to MSO yet; instead schedule a larger-N re-run once Phase 2 "
                     "expands the backtest population (B10/P68-P70 or Q71-Q73).")
    else:
        lines.append("**Real M1 input confirms the M15-fallback null verdict.**")
        lines.append("")
        lines.append("Recommendation: archive the `cumulative_delta` / `footprint_imbalance` / "
                     "`micro_reversal_count` triplet from the active research backlog. The "
                     "synthetic-tick reconstructor as a class is upper-bounded by Lee-Ready 1991 "
                     "candle-direction proxy — adding a longer lookback or different bar "
                     "aggregations is unlikely to change the verdict.")
        lines.append("")
        lines.append("**Strategic note**: per `project_f15_synthesis_regime_is_load_bearing`, "
                     "the H2 decay is regime-conditioned LONG-side selectivity collapse. Phase 2 "
                     "research budget is better spent on (a) regime-aware K54 ML classifier, "
                     "(b) Phase 2 prompt research targeting *regime-conditional selectivity* in "
                     "trending_bull cohort, NOT on OHLC-derivable microstructure features.")
    lines.append("")
    lines.append("## Reconstructor sample (XAUUSD 2026-04-15 13:00-13:30 UTC)")
    lines.append("")
    lines.append(f"- Input timeframe: **{sample_summary.get('input_timeframe')}** "
                 "(was `M15_fallback` in prior run)")
    lines.append(f"- Bars consumed: {sample_summary.get('bars_consumed')}")
    lines.append(f"- Synthetic ticks emitted: {sample_summary.get('ticks_emitted')}")
    lines.append("")
    lines.append("See `reconstructor_validation_m1.csv` for the full 4-tick OHLC path dump.")
    lines.append("")
    lines.append("## Reproducibility")
    lines.append("")
    lines.append("```bash")
    lines.append("# Phase A — backfill M1 from MT5 (requires redacted_account terminal logged in)")
    lines.append("python research/m1_backfill_e24_e26_rerun/backfill_m1.py")
    lines.append("")
    lines.append("# Phase B — re-run E24/E26 with real M1")
    lines.append("python research/m1_backfill_e24_e26_rerun/rerun_e26_m1.py")
    lines.append("```")
    rp.write_text("\n".join(lines), encoding="utf-8")
    return rp


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/6] Harvesting fills from knowledge_base_backtest/sessions/...")
    fills = harvest_fills()
    print(f"     {len(fills)} fills harvested across {len(set(f['symbol'] for f in fills))} symbols")

    print("[2/6] Extracting per-fill microstructure features (REAL M1)...")
    feat_rows, telemetry = extract_features_real_m1(fills)
    print(f"     {len(feat_rows)} feature rows ({telemetry['skipped_fills']} skipped)")
    print(f"     Skip reasons: {telemetry['skip_reasons']}")
    print(f"     Per-symbol skipped: {telemetry['skipped_by_symbol']}")
    print(f"     Input timeframes per symbol: {telemetry['input_timeframes']}")

    print("[3/6] Correlating features with realized R...")
    cell_rows = correlate_features_with_r(feat_rows)
    pooled = aggregate_by_feature(cell_rows)

    survivors = [r for r in cell_rows if r.get("verdict") == "SURVIVES_BONFERRONI"]
    raw_sigs = [r for r in cell_rows if r.get("verdict") == "RAW_SIG_NOT_SURVIVING"]
    print(f"     Bonferroni survivors: {len(survivors)}")
    print(f"     Raw-sig (not surviving): {len(raw_sigs)}")

    print("[4/6] Reconstructor sample dump (real M1)...")
    sample_summary = write_reconstructor_validation_sample()
    print(f"     Wrote {sample_summary['ticks_emitted']} sample ticks "
          f"(input_timeframe={sample_summary['input_timeframe']})")

    print("[5/6] Building comparison vs M15-fallback baseline...")
    prior = load_prior_baseline()
    comparison = build_comparison(cell_rows, prior)

    print("[6/6] Writing artifact bundle...")
    # CSV — per-cell correlations (real M1)
    csv_path = OUT_DIR / "feature_correlations_m1.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["symbol", "feature", "n", "spearman_rho", "p_value", "p_bonferroni", "verdict"])
        for r in cell_rows:
            w.writerow([r["symbol"], r["feature"], r["n"], r["spearman_rho"], r["p_value"], r["p_bonferroni"], r["verdict"]])
    print(f"     Wrote {csv_path}")

    # Per-fill feature dump
    feat_csv = OUT_DIR / "per_fill_features_m1.csv"
    cols = ["fill_id", "symbol", "candle_close_ts", "input_timeframe", "framework",
            "setup_grade", "kill_zone", "outcome", "lookback_bars_used", "lookback_minutes",
            "cumulative_delta", "footprint_imbalance", "micro_reversal_count", "r_multiple"]
    with open(feat_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in feat_rows:
            w.writerow(r)
    print(f"     Wrote {feat_csv}")

    # Per-feature comparison CSV
    comp_csv = OUT_DIR / "per_feature_comparison.csv"
    with open(comp_csv, "w", newline="") as fh:
        cols = ["symbol", "feature", "n_m1", "rho_m1", "p_m1", "p_bf_m1", "verdict_m1",
                "n_m15", "rho_m15", "p_m15", "p_bf_m15", "verdict_m15", "delta_rho_abs"]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for c in comparison:
            w.writerow(c)
    print(f"     Wrote {comp_csv}")

    verdict = determine_global_verdict(cell_rows)

    # JSON results bundle
    results = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "lookback_minutes": LOOKBACK_MIN,
        "telemetry": telemetry,
        "per_cell_correlations": cell_rows,
        "pooled_per_feature": pooled,
        "comparison_vs_m15_fallback": comparison,
        "reconstructor_sample": sample_summary,
        "verdict_code": verdict[0],
        "verdict_narrative": verdict[1],
        "summary": {
            "total_fills_in": telemetry["total_fills_in"],
            "total_features_out": telemetry["total_features_out"],
            "bonferroni_survivors": len(survivors),
            "raw_sig_count": len(raw_sigs),
            "no_signal_cells": sum(1 for r in cell_rows if r.get("verdict") == "NO_SIGNAL"),
            "insufficient_n_cells": sum(1 for r in cell_rows if r.get("verdict") == "INSUFFICIENT_N"),
        },
    }
    json_path = OUT_DIR / "results.json"
    with open(json_path, "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    print(f"     Wrote {json_path}")

    # Markdown report
    backfill_log = OUT_DIR / "m1_backfill_log.csv"
    report_path = write_report(cell_rows, pooled, comparison, telemetry,
                                sample_summary, verdict, backfill_log)
    print(f"     Wrote {report_path}")

    print()
    print("=" * 70)
    print(f"VERDICT: {verdict[0]}")
    print("=" * 70)
    print(verdict[1])
    print()
    print("=== POOLED VERDICT (real M1) ===")
    for p in pooled:
        print(f"  {p['feature']:<25} cells={p['cells_tested']:<2} "
              f"median_rho={p['median_spearman']} "
              f"raw_sig={p['raw_sig_count']} bf={p['bonferroni_survivors']} "
              f"=> {p['verdict']}")
    print()
    print("=== TOP-3 ABSOLUTE RHO PER-CELL (real M1) ===")
    sorted_cells = sorted(
        [r for r in cell_rows if r.get("spearman_rho") is not None],
        key=lambda r: abs(r["spearman_rho"]),
        reverse=True,
    )[:3]
    for r in sorted_cells:
        print(f"  {r['symbol']:<12} {r['feature']:<25} "
              f"rho={r['spearman_rho']:>+6.3f} p={r['p_value']:.4f} "
              f"p_bf={r['p_bonferroni']:.4f} n={r['n']:<3} => {r['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
