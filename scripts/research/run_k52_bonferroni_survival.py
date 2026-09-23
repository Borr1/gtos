#!/usr/bin/env python3
"""K52 — Bonferroni-Survival Re-Test of GTOS Validated Numbers.

Pure-Python CLI that re-runs the five Bonferroni-surviving baseline tests
from CLAUDE.md against the current 2-year dataset.

Strategic question
------------------
Five baseline findings each carry a Bonferroni-corrected p-value computed
on the H1 batch dataset. Do they still survive at the current data?

For each finding, this script:
  1. Loads the per-test inputs from the canonical realized-R sources:
       - ``research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv``
       - ``knowledge_base/index/_trade_index.json``
     plus the per-record OB structural backtest at
       - ``knowledge_base_backtest/analysis/per_record_20260406/ob_per_record_*.csv``
     plus the Test A rerun cached values from
       - ``.context/03_analysis/test_a_rerun_real_bos_results.md`` (verbatim).
  2. Computes raw + Bonferroni-corrected p (family size 5).
  3. Compares against the baseline raw + corrected p in ``TEST_REGISTRY``.
  4. Writes ``survival.json`` (machine-readable) + ``report.md`` (human).

No AI calls. No production-config touched. Read-only on data sources;
writes only inside ``--output-dir``.

Usage:
    python scripts/research/run_k52_bonferroni_survival.py \
        --output-dir research/edge_decomposition/K52_survival
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research_infra.bonferroni_survival import (  # noqa: E402
    FAMILY_SIZE,
    SurvivalReport,
    TEST_REGISTRY,
    TestResult,
    evaluate_survival,
)


DEFAULT_TRADES_UNIFIED_CSV = (
    ROOT / "research" / "b_deep_audit_2026-04-19" / "phase1" / "_delta_scratch"
    / "trades_unified.csv"
)
DEFAULT_TRADE_INDEX_JSON = ROOT / "knowledge_base" / "index" / "_trade_index.json"
DEFAULT_OB_PER_RECORD_DIR = (
    ROOT / "knowledge_base_backtest" / "analysis" / "per_record_20260406"
)


# ────────────────────────────────────────────────────────────────────────────
# Realized-R loaders
# ────────────────────────────────────────────────────────────────────────────

def _load_realized_r_per_instrument(
    trades_unified_csv: Path,
    trade_index_json: Path,
) -> dict[str, list[dict]]:
    """Merge realized-R from ``trades_unified.csv`` + ``_trade_index.json``.

    Returns
    -------
    dict[str, list[dict]]
        Symbol → list of ``{"r": float, "trade_id": str, "date": str,
        "framework": str, "kill_zone": str}``.

    Dedup convention: the trades_unified.csv ``trade_id`` is the bare
    ``bt_<date>_<kz>_<num>`` form; the live ``_trade_index.json`` form
    appends ``_<symbol_lower>``. Two entries are considered duplicates
    iff stripping the ``_<symbol>`` suffix from the index entry yields
    the unified entry's ``trade_id`` (verified empirically against the
    data: 105/105 _trade_index XAU records match a unified entry on
    date+kz; the trailing-symbol stripping is the canonical dedup key).
    """
    out: dict[str, list[dict]] = {}
    seen_ids: set[str] = set()

    if trades_unified_csv.exists():
        with trades_unified_csv.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = (row.get("symbol") or "").strip().upper()
                tid = (row.get("trade_id") or "").strip()
                r_raw = row.get("r_multiple")
                if not sym or not tid or r_raw in (None, "", "None"):
                    continue
                try:
                    r = float(r_raw)
                except ValueError:
                    continue
                if not math.isfinite(r):
                    continue
                seen_ids.add(tid)
                out.setdefault(sym, []).append({
                    "r": r,
                    "trade_id": tid,
                    "date": row.get("date"),
                    "framework": row.get("framework"),
                    "kill_zone": row.get("kill_zone"),
                })

    if trade_index_json.exists():
        try:
            doc = json.loads(trade_index_json.read_text(encoding="utf-8"))
        except Exception:
            doc = None
        if isinstance(doc, dict):
            trades = doc.get("trades")
            if isinstance(trades, list):
                for t in trades:
                    if not isinstance(t, dict):
                        continue
                    sym = (t.get("symbol") or "").strip().upper()
                    tid = (t.get("trade_id") or "").strip()
                    r_raw = t.get("r_multiple")
                    if not sym or not tid or r_raw is None:
                        continue
                    try:
                        r = float(r_raw)
                    except (TypeError, ValueError):
                        continue
                    if not math.isfinite(r):
                        continue
                    # Dedup: strip trailing _<symbol_lower> if present
                    suffix = f"_{sym.lower()}"
                    bare_tid = tid[:-len(suffix)] if tid.endswith(suffix) else tid
                    if bare_tid in seen_ids or tid in seen_ids:
                        continue
                    seen_ids.add(tid)
                    seen_ids.add(bare_tid)
                    out.setdefault(sym, []).append({
                        "r": r,
                        "trade_id": tid,
                        "date": t.get("date"),
                        "framework": t.get("framework"),
                        "kill_zone": t.get("kill_zone"),
                    })

    return out


# ────────────────────────────────────────────────────────────────────────────
# Test A rerun cached values (OB zone vs 80% pullback)
# ────────────────────────────────────────────────────────────────────────────

# These come verbatim from `.context/03_analysis/test_a_rerun_real_bos_results.md`
# Q2: "Does the OB zone add value over generic deep pullback?"
#   OB sim:       122/173  (resolved wins / resolved trials)
#   80% retrace:   73/136
#   Fisher p (apples-to-apples) = 0.0029 (OB vs 80% baseline)
#
# Until a fresh Test A re-run is committed against the H2-2026 data, the
# "current" inputs equal the baseline inputs (the test is not actually
# being re-evaluated on new data — see report caveats). The assertion the
# verdict block makes is whether the OB-zone advantage still SURVIVES
# Bonferroni at family size 5 under K52's standardised pooled-z test
# (different test from the original Fisher exact, hence p may differ).
TEST_A_RERUN_OB_WINS = 122
TEST_A_RERUN_OB_N = 173
TEST_A_RERUN_BASE_WINS = 73
TEST_A_RERUN_BASE_N = 136


# ────────────────────────────────────────────────────────────────────────────
# OB-per-record loader (FVG-in-impulse signal)
# ────────────────────────────────────────────────────────────────────────────

def _load_fvg_in_impulse_per_instrument(
    per_record_dir: Path,
) -> dict[str, dict]:
    """Build the ``fvg_in_impulse_per_instrument`` data block.

    For each per-instrument ``ob_per_record_<symbol>.csv`` available:
      - Filter to OBs with ``retested == True`` and a non-empty
        ``continuation`` outcome.
      - Split by ``impulse_created_fvg`` flag (True = FVG-in-impulse,
        False = non-FVG-impulse OB).
      - Count ``continuation == True`` as a win in each bucket.

    A "win" here is the structural-continuation outcome (price continues
    in impulse direction post-retest), the same metric used in the
    original CLAUDE.md "+7-20pp across 6 instruments" claim. This is
    structural WR — not realized R. The K52 report flags this in
    caveats so the reader does not conflate the two layers.

    Returns
    -------
    dict
        ``{<INSTRUMENT>: {"fvg_wins": int, "fvg_n": int,
                          "non_wins": int, "non_n": int}}``
    """
    out: dict[str, dict] = {}
    if not per_record_dir.exists():
        return out

    for fp in sorted(per_record_dir.glob("ob_per_record_*.csv")):
        # Filename like ob_per_record_xauusd.csv
        stem = fp.stem  # ob_per_record_xauusd
        if not stem.startswith("ob_per_record_"):
            continue
        sym = stem[len("ob_per_record_"):].upper()
        if not sym:
            continue
        try:
            with fp.open(encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        except Exception:
            continue

        fvg_wins = fvg_n = non_wins = non_n = 0
        for r in rows:
            retested = (r.get("retested") or "").strip().lower()
            if retested != "true":
                continue
            cont_raw = (r.get("continuation") or "").strip().lower()
            if cont_raw not in ("true", "false"):
                continue
            is_win = cont_raw == "true"
            flag = (r.get("impulse_created_fvg") or "").strip().lower()
            if flag == "true":
                fvg_n += 1
                if is_win:
                    fvg_wins += 1
            elif flag == "false":
                non_n += 1
                if is_win:
                    non_wins += 1
            # Else: empty / unknown — skip
        if fvg_n == 0 and non_n == 0:
            continue
        out[sym] = {
            "fvg_wins": fvg_wins,
            "fvg_n": fvg_n,
            "non_wins": non_wins,
            "non_n": non_n,
        }
    return out


# ────────────────────────────────────────────────────────────────────────────
# Data assembly
# ────────────────────────────────────────────────────────────────────────────

def _build_data_dict(
    *,
    trades_unified_csv: Path,
    trade_index_json: Path,
    per_record_dir: Path,
) -> tuple[dict, dict]:
    """Build the data dict for ``evaluate_survival`` and a provenance block.

    Returns
    -------
    (data, provenance)
        ``data`` is the dict with the four expected blocks ready for the
        registry. ``provenance`` records what file each block came from
        (written into the report for auditability).
    """
    realized = _load_realized_r_per_instrument(trades_unified_csv, trade_index_json)
    fvg = _load_fvg_in_impulse_per_instrument(per_record_dir)

    def _block_for(sym: str) -> dict | None:
        trades = realized.get(sym)
        if not trades:
            return None
        wins = sum(1 for t in trades if t.get("r", 0) > 0)
        n = len(trades)
        return {"wins": wins, "n": n, "filled_trades_sample_size": n}

    data: dict = {}
    block = _block_for("XAUUSD")
    if block is not None:
        data["xau_ob_retest"] = block
    block = _block_for("US30_CASH") or _block_for("US30")
    if block is not None:
        data["us30_ob_retest"] = block
    block = _block_for("USDJPY")
    if block is not None:
        data["usdjpy_ob_retest"] = block

    data["ob_zone_vs_baseline_80pct"] = {
        "ob_wins": TEST_A_RERUN_OB_WINS,
        "ob_n": TEST_A_RERUN_OB_N,
        "base_wins": TEST_A_RERUN_BASE_WINS,
        "base_n": TEST_A_RERUN_BASE_N,
    }
    if fvg:
        data["fvg_in_impulse_per_instrument"] = fvg

    provenance = {
        "trades_unified_csv": str(trades_unified_csv.resolve()),
        "trade_index_json": str(trade_index_json.resolve()),
        "ob_per_record_dir": str(per_record_dir.resolve()),
        "test_a_rerun_source": (
            ".context/03_analysis/test_a_rerun_real_bos_results.md (cached values)"
        ),
        "realized_r_per_symbol_n": {
            sym: len(ts) for sym, ts in realized.items()
        },
        "fvg_in_impulse_per_symbol": {
            sym: blk for sym, blk in fvg.items()
        },
    }
    return data, provenance


# ────────────────────────────────────────────────────────────────────────────
# Output writers
# ────────────────────────────────────────────────────────────────────────────

def _format_p(p: float) -> str:
    if p is None or (isinstance(p, float) and not math.isfinite(p)):
        return "—"
    if p < 1e-4:
        return f"{p:.2e}"
    return f"{p:.4f}"


def _format_pct(x: float) -> str:
    if not math.isfinite(x):
        return "—"
    return f"{x * 100.0:.2f}%"


def _result_to_dict(r: TestResult) -> dict:
    return {
        "spec_key": r.spec_key,
        "spec_label": r.spec_label,
        "baseline_raw_p": r.baseline_raw_p,
        "baseline_corrected_p": r.baseline_corrected_p,
        "current_n": r.current_n,
        "current_raw_p": _round_or_none(r.current_raw_p),
        "current_corrected_p": _round_or_none(r.current_corrected_p),
        "current_summary": _sanitise_summary(r.current_summary),
        "status": r.status,
        "notes": r.notes,
    }


def _round_or_none(x: float, digits: int = 8) -> float | None:
    if x is None:
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return round(float(x), digits)


def _sanitise_summary(summary: dict) -> dict:
    """Make the summary dict JSON-serialisable + finite-float-clean."""
    if not isinstance(summary, dict):
        return {}
    out: dict = {}
    for k, v in summary.items():
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                out[k] = None
            else:
                out[k] = round(v, 8)
        elif isinstance(v, list):
            out[k] = [_sanitise_summary(item) if isinstance(item, dict) else item
                      for item in v]
        elif isinstance(v, dict):
            out[k] = _sanitise_summary(v)
        else:
            out[k] = v
    return out


def _write_survival_json(out_dir: Path, report: SurvivalReport, provenance: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "survival.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "family_size": report.family_size,
        "alpha": report.alpha,
        "n_min": report.n_min,
        "results": [_result_to_dict(r) for r in report.results],
        "surviving_keys": list(report.surviving),
        "failed_keys": list(report.failed),
        "insufficient_keys": list(report.insufficient),
        "provenance": provenance,
    }
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return fp


def _write_report(
    out_dir: Path,
    report: SurvivalReport,
    provenance: dict,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "report.md"

    lines: list[str] = []
    lines.append("# K52 — Bonferroni-Survival Re-Test")
    lines.append("")
    lines.append(f"_Generated: {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(
        "Re-running the five Bonferroni-surviving baseline findings from "
        "CLAUDE.md against the current dataset, with Bonferroni correction "
        f"applied at the canonical family size = **{report.family_size}**."
    )
    lines.append("")
    lines.append("## Bonferroni-survival re-test (H1 batch → current 2026 data)")
    lines.append("")
    lines.append("| Finding | H1 raw p | H1 corrected p | Current raw p | Current corrected p | Status |")
    lines.append("|---|---|---|---|---|---|")
    for r in report.results:
        lines.append(
            f"| {r.spec_label} "
            f"| {_format_p(r.baseline_raw_p)} "
            f"| {_format_p(r.baseline_corrected_p)} "
            f"| {_format_p(r.current_raw_p)} "
            f"| {_format_p(r.current_corrected_p)} "
            f"| {r.status} |"
        )
    lines.append("")

    # Summary block matching the requested verdict format
    n_surv = len(report.surviving)
    n_total = len(report.results)
    failed_labels = [
        next(rr.spec_label for rr in report.results if rr.spec_key == k)
        for k in report.failed
    ]
    insuff_labels = [
        next(rr.spec_label for rr in report.results if rr.spec_key == k)
        for k in report.insufficient
    ]

    lines.append("## Strategic verdict")
    lines.append("")
    lines.append(f"Findings still surviving: **{n_surv} / {n_total}**")
    if failed_labels:
        lines.append("")
        lines.append(f"Findings that failed: **{', '.join(failed_labels)}**")
    if insuff_labels:
        lines.append("")
        lines.append(
            f"Findings with insufficient data / NO_DATA: "
            f"**{', '.join(insuff_labels)}**"
        )
    lines.append("")
    lines.append("**Reasoning:**")
    lines.append("")
    lines.append(_strategic_reasoning(report, provenance))
    lines.append("")

    # Per-finding detail
    lines.append("## Per-finding detail")
    lines.append("")
    for r in report.results:
        lines.append(f"### {r.spec_label} — `{r.spec_key}` → {r.status}")
        lines.append("")
        lines.append(f"- **Baseline (CLAUDE.md):** raw p = `{_format_p(r.baseline_raw_p)}`, "
                     f"corrected p = `{_format_p(r.baseline_corrected_p)}`")
        lines.append(f"- **Current data:** raw p = `{_format_p(r.current_raw_p)}`, "
                     f"corrected p = `{_format_p(r.current_corrected_p)}`")
        lines.append(f"- **Current n:** {r.current_n}")
        if r.current_summary:
            lines.append(f"- **Summary:** `{json.dumps(_sanitise_summary(r.current_summary))}`")
        lines.append(f"- **Notes:** {r.notes}")
        lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "- **One-sample WR vs breakeven** (XAUUSD / US30 / USDJPY): exact "
        "two-sided binomial test against H0: WR = 50%. Wins = realised R > 0; "
        "BE counts as a loss (matches GTOS WR convention)."
    )
    lines.append(
        "- **OB zone advantage**: pooled-variance two-proportion z-test "
        "comparing OB-sim WR (122/173) vs 80%-retrace baseline sim WR "
        "(73/136) on the Test A rerun population. Inputs are cached from "
        "`.context/03_analysis/test_a_rerun_real_bos_results.md` until a "
        "fresh re-run is committed."
    )
    lines.append(
        "- **FVG-in-impulse**: pooled two-proportion z-test on the union of "
        "per-instrument FVG-in-impulse OBs (continuation = win) vs non-FVG-"
        "impulse OBs from the per-record OB structural backtest "
        "(`knowledge_base_backtest/analysis/per_record_20260406/ob_per_record_*.csv`). "
        "A sign-test on the count of instruments with positive delta is "
        "reported in the summary alongside the pooled-z primary p."
    )
    lines.append(
        f"- **Bonferroni correction**: corrected p = min(1, raw p × "
        f"{report.family_size}). Family size is fixed at the pre-registered "
        "5; tests that cannot be run still consume their α/5 share. This is "
        "the conservative pre-registered choice."
    )
    lines.append(
        f"- **Decision rule**: SURVIVES iff corrected p < α = {report.alpha} "
        f"AND n ≥ n_min = {report.n_min}. Below the n_min floor, status is "
        "INSUFFICIENT_N regardless of p."
    )
    lines.append("")

    # Provenance
    lines.append("## Data provenance")
    lines.append("")
    lines.append(f"- Realized R (XAUUSD / GBPUSD): `{provenance['trades_unified_csv']}`")
    lines.append(f"- Live trade index (XAUUSD / GBPUSD): `{provenance['trade_index_json']}`")
    lines.append(f"- OB per-record (FVG-in-impulse): `{provenance['ob_per_record_dir']}`")
    lines.append(f"- Test A rerun cache: `{provenance['test_a_rerun_source']}`")
    lines.append("")
    lines.append("**Realized R per symbol:**")
    for sym, n in sorted(provenance.get("realized_r_per_symbol_n", {}).items()):
        lines.append(f"  - {sym}: n = {n}")
    lines.append("")

    # Caveats
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "- **Test methodology vs CLAUDE.md baselines.** The published baseline "
        "p-values were computed by historical scripts that may have used "
        "different tests (Fisher exact / chi-square / one-sided). K52 "
        "standardises on exact two-sided binomial (one-sample) and pooled-"
        "variance two-proportion z (two-sample). Current vs baseline p "
        "differences may reflect either real decay OR test-methodology drift."
    )
    lines.append(
        "- **FVG-in-impulse is structural WR.** The current-data inputs use "
        "OB *continuation* outcomes (price moves in impulse direction post-"
        "retest), not realised R per fill. This matches the original CLAUDE.md "
        "+7-20pp signal layer (cross-instrument continuation), which is "
        "orthogonal to realised-R one-sample tests above. Do not conflate."
    )
    lines.append(
        "- **OB-zone advantage uses cached Test A inputs.** Until a fresh "
        "Test A rerun is committed against H2-2026 data, this test re-"
        "evaluates the *same population* under K52's standardised pooled-z "
        "test. A SURVIVES verdict here means the OB-zone signal still "
        "rejects H0 under the standardised test — it does NOT mean the "
        "Test A rerun has been re-executed. Re-run Test A to get a true "
        "current-data verdict."
    )
    lines.append(
        "- **Realized R limited to XAUUSD + GBPUSD.** Under the FTMO free-"
        "trial EA exclusion, no live fills exist on US30 / USDJPY / GBPJPY / "
        "XAGUSD / NAS100. Those tests will status NO_DATA / INSUFFICIENT_N "
        "until paid-challenge fills accumulate (≥30 per instrument). Treat "
        "the current verdict for those three as 'cannot tell yet'."
    )
    lines.append(
        "- **Family size 5 is hard-coded.** Any change to the family must "
        "go through ADR + amend CLAUDE.md Validated Numbers — adding tests "
        "post-hoc inflates α budget without honest pre-registration."
    )
    lines.append("")

    # K54 implications
    lines.append("## K54 ML model implications")
    lines.append("")
    lines.append(
        "K54 (downstream feature-selection) uses K52 outcomes as a selection "
        "prior. A finding that fails survival is a feature that has lost "
        "discrimination on current data:"
    )
    lines.append("")
    lines.append("- **SURVIVES** → contribute the corresponding feature with full weight.")
    lines.append(
        "- **FAILS** → drop or aggressively regularise the feature. The "
        "signal that minted the feature has lost discrimination."
    )
    lines.append(
        "- **INSUFFICIENT_N / NO_DATA** → hold in reserve. Re-run K52 "
        "quarterly; promote on re-survival."
    )
    lines.append("")
    if failed_labels:
        lines.append(f"K54 should down-weight features tied to: {', '.join(failed_labels)}.")
        lines.append("")
    if insuff_labels:
        lines.append(
            f"K54 should hold (not actively use, not delete) features tied to: "
            f"{', '.join(insuff_labels)}. Re-evaluate after live-fill accumulation."
        )
        lines.append("")

    fp.write_text("\n".join(lines), encoding="utf-8")
    return fp


def _strategic_reasoning(report: SurvivalReport, provenance: dict) -> str:
    """Build a 2-4 sentence interpretation for the verdict block."""
    n_surv = len(report.surviving)
    n_fail = len(report.failed)
    n_insuff = len(report.insufficient)
    parts: list[str] = []

    if n_surv == len(report.results):
        parts.append(
            "All five baseline findings still survive Bonferroni correction at "
            "the current dataset; the Validated Numbers in CLAUDE.md remain the "
            "working baseline. Decay (per item #4) is concentrated outside "
            "this five-finding family — likely in instrument-conditional / "
            "regime-conditional cells not covered by these aggregate tests."
        )
    elif n_fail == len(report.results):
        parts.append(
            "ALL five baseline findings FAIL Bonferroni at the current "
            "dataset. The Validated Numbers in CLAUDE.md are stale and must "
            "be revised in the same commit. K54 should treat the ML-feature "
            "set as fully unmoored from CLAUDE.md priors."
        )
    elif n_fail > 0:
        parts.append(
            f"{n_fail} of {len(report.results)} baseline findings FAIL "
            f"Bonferroni at the current dataset; {n_surv} still survive. "
            "The failed findings' headline numbers in CLAUDE.md are stale "
            "and must be revised in the same commit. K54 should drop / "
            "regularise the corresponding features. Surviving findings remain "
            "the working baseline."
        )
    else:
        parts.append(
            f"{n_surv} of {len(report.results)} baseline findings survive "
            "Bonferroni at the current dataset; the rest are INSUFFICIENT_N "
            "or NO_DATA. The non-survivors are not failures of the edge — "
            "they are data-availability gaps reflecting the FTMO free-trial "
            "EA exclusion. Re-run K52 after paid-challenge fills accumulate."
        )

    if n_insuff > 0 and n_fail > 0:
        parts.append(
            f"Additionally, {n_insuff} finding(s) have insufficient data to "
            "draw a verdict — re-run K52 after fills accumulate."
        )
    elif n_insuff > 0:
        parts.append(
            f"Note: {n_insuff} finding(s) have insufficient current-data "
            "fills to support a verdict; re-run K52 quarterly."
        )

    return " ".join(parts)


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory to write survival.json + report.md.",
    )
    parser.add_argument(
        "--trades-unified-csv",
        default=str(DEFAULT_TRADES_UNIFIED_CSV),
        help="Path to trades_unified.csv (default: research/b_deep_audit_2026-04-19/...).",
    )
    parser.add_argument(
        "--trade-index-json",
        default=str(DEFAULT_TRADE_INDEX_JSON),
        help="Path to _trade_index.json (default: knowledge_base/index/_trade_index.json).",
    )
    parser.add_argument(
        "--ob-per-record-dir",
        default=str(DEFAULT_OB_PER_RECORD_DIR),
        help="Directory with ob_per_record_<symbol>.csv files.",
    )
    parser.add_argument(
        "--alpha", type=float, default=0.05,
        help="Bonferroni-corrected significance threshold (default: 0.05).",
    )
    parser.add_argument(
        "--n-min", type=int, default=20,
        help="Minimum n for non-INSUFFICIENT_N verdicts (default: 20).",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir).resolve()
    trades_unified_csv = Path(args.trades_unified_csv).resolve()
    trade_index_json = Path(args.trade_index_json).resolve()
    per_record_dir = Path(args.ob_per_record_dir).resolve()

    print(f"[K52] trades_unified_csv = {trades_unified_csv}", file=sys.stderr)
    print(f"[K52] trade_index_json   = {trade_index_json}", file=sys.stderr)
    print(f"[K52] per_record_dir     = {per_record_dir}", file=sys.stderr)
    print(f"[K52] output_dir         = {out_dir}", file=sys.stderr)

    data, provenance = _build_data_dict(
        trades_unified_csv=trades_unified_csv,
        trade_index_json=trade_index_json,
        per_record_dir=per_record_dir,
    )

    print(f"[K52] data blocks present: {sorted(data.keys())}", file=sys.stderr)
    for sym, n in sorted(provenance.get("realized_r_per_symbol_n", {}).items()):
        print(f"[K52]   realized_r {sym}: n = {n}", file=sys.stderr)

    report = evaluate_survival(
        TEST_REGISTRY, data,
        family_size=FAMILY_SIZE,
        alpha=args.alpha, n_min=args.n_min,
    )

    survival_fp = _write_survival_json(out_dir, report, provenance)
    report_fp = _write_report(out_dir, report, provenance)
    print(f"[K52] wrote {survival_fp}", file=sys.stderr)
    print(f"[K52] wrote {report_fp}", file=sys.stderr)
    print(
        f"[K52] verdict: {len(report.surviving)}/{len(report.results)} "
        f"surviving; failed={list(report.failed)}; "
        f"insufficient={list(report.insufficient)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
