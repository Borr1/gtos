"""A5 — Regime-Stratified WR Matrix CLI.

Aggregates every realized CANDIDATE from the project's backtest /
simulation outputs (``research/**/all_results*.json``), tags each one
with the v2 H4 regime active at its candle-close time (sourced from
``shadow_logs/structure_detector_divergences.jsonl``), and emits:

* ``matrix.json`` — per-cell stats (n, WR, ExpR, median, Wilson 95% CI,
  LOW_N flag) plus an aggregate summary (best/worst regime, untagged
  fraction).
* ``cands_with_regime.jsonl`` — every CAND with its regime tag (this
  is the K54 ML-classifier feature input).
* ``report.md`` — heatmap-friendly per-instrument x regime table + the
  strategic verdict block.

Usage::

    python scripts/research/run_a5_regime_matrix.py \
        --output-dir research/decay_diagnostic/A5_regime_matrix \
        [--structure-log shadow_logs/structure_detector_divergences.jsonl] \
        [--results-glob "research/**/all_results*.json"]

The script is offline-only (no MT5, no Anthropic API, $0 spend).
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

# Make the worktree's project root importable when the CLI is invoked from
# anywhere via ``python scripts/research/run_a5_regime_matrix.py``.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.regime_matrix import (  # noqa: E402
    LOW_N_THRESHOLD,
    UNTAGGED,
    RegimeIndex,
    RegimeMatrix,
    build_wr_matrix,
    iter_cands_from_all_results,
    load_regime_index,
)

logger = logging.getLogger("a5_regime_matrix")

#: Default output target.
DEFAULT_OUTPUT_DIR = "research/decay_diagnostic/A5_regime_matrix"

#: Default glob for backtest result files (relative to project root).
DEFAULT_RESULTS_GLOB = "research/**/all_results*.json"

#: Default location of the structure detector shadow log (gitignored).
DEFAULT_STRUCTURE_LOG = "shadow_logs/structure_detector_divergences.jsonl"


# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the A5 regime-stratified WR matrix from realized CANDs."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Directory to write matrix.json, cands_with_regime.jsonl, "
            "and report.md (default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--structure-log",
        default=DEFAULT_STRUCTURE_LOG,
        help=(
            "Path to structure_detector_divergences.jsonl "
            "(default: %(default)s; gitignored runtime artefact)."
        ),
    )
    parser.add_argument(
        "--results-glob",
        default=DEFAULT_RESULTS_GLOB,
        help=(
            "Glob pattern (recursive) for all_results*.json files "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--results-paths",
        nargs="*",
        default=None,
        help=(
            "Explicit list of all_results*.json files. If supplied, "
            "overrides --results-glob."
        ),
    )
    parser.add_argument(
        "--freshness-hours",
        type=int,
        default=6,
        help=(
            "Maximum staleness for an H4 row to count as the active regime. "
            "Default: %(default)s."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO logging.",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Output: matrix.json
# ---------------------------------------------------------------------------


def _matrix_to_json(matrix: RegimeMatrix) -> dict:
    """Serialise a RegimeMatrix into the matrix.json schema."""
    cells_payload = []
    for (instrument, regime), stats in sorted(matrix.cells.items()):
        cells_payload.append(
            {
                "instrument": instrument,
                "regime": regime,
                "n": stats["n"],
                "wins": stats["wins"],
                "wr": stats["wr"],
                "exp_r_arith": stats["exp_r_arith"],
                "median_r": stats["median_r"],
                "min_r": stats["min_r"],
                "max_r": stats["max_r"],
                "wilson_ci_95": [stats["wilson_lo"], stats["wilson_hi"]],
                "low_n": stats["n"] < LOW_N_THRESHOLD,
            }
        )
    return {
        "schema_version": 1,
        "instruments": matrix.instruments,
        "regimes": matrix.regimes,
        "cells": cells_payload,
        "summary": matrix.summary(),
        "low_n_threshold": LOW_N_THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Output: cands_with_regime.jsonl
# ---------------------------------------------------------------------------


def _cand_to_jsonl(
    cand: dict,
    regime: str,
    *,
    keys_keep: tuple[str, ...] = (
        "symbol",
        "candle_close_time",
        "candle_time",
        "kill_zone",
        "decision",
        "direction",
        "setup_grade",
        "h1_direction",
        "bias",
        "bias_source",
        "outcome",
        "r_multiple",
        "exit_candle",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "l2_passed",
        "p2a_decision",
        "source_file",
    ),
) -> dict:
    """Project a CAND record onto the K54 feature schema + regime tag."""
    row = {k: cand.get(k) for k in keys_keep if k in cand}
    row["regime"] = regime
    return row


# ---------------------------------------------------------------------------
# Output: report.md
# ---------------------------------------------------------------------------


def _format_pct(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x * 100.0:.1f}%"


def _format_r(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x:+.3f}R"


def _matrix_to_report(
    matrix: RegimeMatrix,
    *,
    structure_log: Path,
    results_count: int,
    skipped_no_outcome: int,
    by_instrument_coverage: dict[str, int],
    by_instrument_regime_n: dict[str, dict[str, int]],
    h4_rows_indexed: int,
    h4_rows_skipped_no_symbol: int,
) -> str:
    """Emit the heatmap-style markdown report + verdict block."""
    summary = matrix.summary()
    lines: list[str] = []
    lines.append("# A5 — Regime-Stratified WR Matrix")
    lines.append("")
    lines.append(f"**Total CANDs (with realized R)**: {matrix.total_cands}")
    lines.append(
        f"**UNTAGGED**: {matrix.untagged_count} "
        f"({_format_pct(summary['untagged_fraction'])})"
    )
    lines.append(f"**Realized-R-missing skipped**: {skipped_no_outcome}")
    lines.append(f"**Result files scanned**: {results_count}")
    lines.append(f"**Structure log**: `{structure_log}`")
    lines.append(
        f"**H4 rows indexed**: {h4_rows_indexed} "
        f"(skipped no-symbol: {h4_rows_skipped_no_symbol})"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Per-instrument tables
    # ------------------------------------------------------------------
    lines.append("## Per-instrument x regime table")
    lines.append("")
    lines.append("Cells: `WR (n) [ExpR] CI95` — ⚠ flag indicates n < {0}.".format(
        LOW_N_THRESHOLD
    ))
    lines.append("")
    # Build the column header from the union of regimes (sorted, plus
    # UNTAGGED last).
    regime_order = [r for r in matrix.regimes if r != UNTAGGED]
    regime_order.sort()
    if UNTAGGED in matrix.regimes:
        regime_order.append(UNTAGGED)

    header = "| Instrument | " + " | ".join(regime_order) + " | Total |"
    sep = "|" + "---|" * (len(regime_order) + 2)
    lines.append(header)
    lines.append(sep)

    instr_n_total: dict[str, int] = {}
    for instrument in matrix.instruments:
        cells_for_instr = []
        total_n = 0
        for regime in regime_order:
            cell = matrix.cells.get((instrument, regime))
            if cell is None or cell["n"] == 0:
                cells_for_instr.append("—")
                continue
            n = cell["n"]
            total_n += n
            wr = cell["wr"]
            exp_r = cell["exp_r_arith"]
            lo, hi = cell["wilson_lo"], cell["wilson_hi"]
            flag = " ⚠" if n < LOW_N_THRESHOLD else ""
            cells_for_instr.append(
                f"{_format_pct(wr)} (n={n}) [{_format_r(exp_r)}] "
                f"[{_format_pct(lo)}-{_format_pct(hi)}]{flag}"
            )
        instr_n_total[instrument] = total_n
        lines.append(
            f"| {instrument} | " + " | ".join(cells_for_instr) + f" | {total_n} |"
        )

    lines.append("")

    # ------------------------------------------------------------------
    # Per-regime aggregate row
    # ------------------------------------------------------------------
    lines.append("## Per-regime aggregate (avg WR across instruments, n>=10 only)")
    lines.append("")
    lines.append("| Regime | Avg WR | Total n | Cells contributing |")
    lines.append("|---|---|---|---|")
    for regime in regime_order:
        avg = summary["regime_avg_wr"].get(regime)
        n_total = summary["regime_total_n"].get(regime, 0)
        contributing = sum(
            1
            for instr in matrix.instruments
            if (instr, regime) in matrix.cells
            and matrix.cells[(instr, regime)]["n"] >= LOW_N_THRESHOLD
        )
        lines.append(
            f"| {regime} | {_format_pct(avg)} | {n_total} | {contributing} |"
        )
    lines.append("")

    # ------------------------------------------------------------------
    # Per-instrument coverage line
    # ------------------------------------------------------------------
    lines.append("## Per-instrument coverage (regimes with n>=10)")
    lines.append("")
    for instrument in matrix.instruments:
        regs_with_enough = [
            r
            for r in matrix.regimes
            if (instrument, r) in matrix.cells
            and matrix.cells[(instrument, r)]["n"] >= LOW_N_THRESHOLD
        ]
        all_regs_count = sum(
            1
            for r in matrix.regimes
            if (instrument, r) in matrix.cells
        )
        lines.append(
            f"- **{instrument}**: {len(regs_with_enough)}/{all_regs_count} "
            f"regimes have n>=10 ({', '.join(sorted(regs_with_enough)) or '-'})"
        )
    lines.append("")

    # ------------------------------------------------------------------
    # Verdict block
    # ------------------------------------------------------------------
    lines.append("---")
    lines.append("")
    lines.append("## Strategic verdict")
    lines.append("")
    if summary["best_regime"] is None or summary["worst_regime"] is None:
        lines.append("- Highest-WR regime: **n/a** (no regime has any "
                     "non-LOW_N cell)")
        lines.append("- Lowest-WR regime: **n/a**")
        lines.append("- WR delta: **n/a**")
        verdict = "INCONCLUSIVE"
        reason = (
            "No regime has any cell with n>=10; cannot rank regime-level "
            "WR. Increase the CAND population (extend backtest period or "
            "broaden instrument set) and rerun."
        )
    else:
        lines.append(
            f"- Highest-WR regime (across instruments): **{summary['best_regime']}** "
            f"(avg WR {_format_pct(summary['best_avg_wr'])})"
        )
        lines.append(
            f"- Lowest-WR regime: **{summary['worst_regime']}** "
            f"(avg WR {_format_pct(summary['worst_avg_wr'])})"
        )
        delta_pp = summary["wr_delta_pp"] or 0.0
        lines.append(
            f"- WR delta between best and worst regime: **{delta_pp:.1f}pp**"
        )
        # Diagnosis policy:
        #   delta >= 15pp -> REGIME_DEPENDENT
        #   delta < 5pp   -> REGIME_AGNOSTIC
        #   else          -> INCONCLUSIVE
        if delta_pp >= 15.0:
            verdict = "REGIME_DEPENDENT"
            reason = (
                f"WR delta of {delta_pp:.1f}pp between '{summary['best_regime']}' "
                f"({_format_pct(summary['best_avg_wr'])}) and '{summary['worst_regime']}' "
                f"({_format_pct(summary['worst_avg_wr'])}) exceeds the 15pp "
                "threshold. Regime-aware sizing (H38) is the warranted "
                "follow-up."
            )
        elif delta_pp < 5.0:
            verdict = "REGIME_AGNOSTIC"
            reason = (
                f"WR delta of {delta_pp:.1f}pp is below the 5pp threshold. "
                "OB-zone edge does not appear regime-dependent at this "
                "sample size; decay must come from elsewhere."
            )
        else:
            verdict = "INCONCLUSIVE"
            reason = (
                f"WR delta of {delta_pp:.1f}pp falls in the [5pp, 15pp) "
                "ambiguous band — neither clearly regime-dependent nor "
                "agnostic. More CANDs / additional regime granularity "
                "needed before acting."
            )

    lines.append(f"- Diagnosis: **{verdict}**")
    lines.append(f"- Reasoning: {reason}")
    lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _resolve_results_paths(
    *,
    explicit: list[str] | None,
    pattern: str,
    project_root: Path,
) -> list[Path]:
    if explicit:
        return [Path(p) for p in explicit]
    # glob.glob with recursive=True requires '**' inside the pattern. If the
    # caller passes a relative pattern, anchor it under the project root;
    # otherwise honour the absolute pattern as-is.
    pattern_path = Path(pattern)
    if pattern_path.is_absolute():
        abs_pattern = pattern
    else:
        abs_pattern = str(project_root / pattern)
    matches = glob.glob(abs_pattern, recursive=True)
    return [Path(m) for m in sorted(matches)]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    project_root = _PROJECT_ROOT
    structure_log = Path(args.structure_log)
    if not structure_log.is_absolute():
        structure_log = project_root / structure_log
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading regime index from %s", structure_log)
    regime_index = load_regime_index(structure_log)
    logger.info(
        "Indexed %d H4 rows; %d skipped (no symbol); %d skipped (no regime)",
        regime_index.h4_rows_indexed,
        regime_index.h4_rows_skipped_no_symbol,
        regime_index.h4_rows_skipped_no_regime,
    )

    results_paths = _resolve_results_paths(
        explicit=args.results_paths,
        pattern=args.results_glob,
        project_root=project_root,
    )
    logger.info("Found %d all_results*.json files", len(results_paths))

    # Stream CANDs once to write the per-CAND JSONL with regime tags, and
    # collect them for matrix aggregation in a single pass.
    cands_with_regime: list[dict] = []
    out_jsonl_path = output_dir / "cands_with_regime.jsonl"
    skipped_no_outcome = 0
    by_instrument_coverage: Counter = Counter()
    by_instrument_regime_n: dict[str, dict[str, int]] = defaultdict(dict)

    with out_jsonl_path.open("w", encoding="utf-8") as out_jsonl:
        for cand in iter_cands_from_all_results(
            results_paths, realised_only=False
        ):
            r = cand.get("r_multiple")
            if not isinstance(r, (int, float)):
                skipped_no_outcome += 1
                continue
            from src.research_infra.regime_matrix import assign_regime_to_cand

            regime = assign_regime_to_cand(
                cand, regime_index, freshness_hours=args.freshness_hours
            )
            row = _cand_to_jsonl(cand, regime)
            out_jsonl.write(json.dumps(row) + "\n")
            cands_with_regime.append({**cand, "regime": regime})
            by_instrument_coverage[cand.get("symbol", "?")] += 1
            by_instrument_regime_n[cand.get("symbol", "?")][regime] = (
                by_instrument_regime_n[cand.get("symbol", "?")].get(regime, 0) + 1
            )

    matrix = build_wr_matrix(
        cands_with_regime, regime_index, freshness_hours=args.freshness_hours
    )

    # Write matrix.json
    matrix_payload = _matrix_to_json(matrix)
    matrix_payload["meta"] = {
        "structure_log": str(structure_log),
        "result_files_scanned": len(results_paths),
        "freshness_hours": args.freshness_hours,
        "skipped_no_outcome": skipped_no_outcome,
        "h4_rows_indexed": regime_index.h4_rows_indexed,
        "h4_rows_skipped_no_symbol": regime_index.h4_rows_skipped_no_symbol,
        "h4_rows_skipped_no_regime": regime_index.h4_rows_skipped_no_regime,
    }
    (output_dir / "matrix.json").write_text(
        json.dumps(matrix_payload, indent=2) + "\n", encoding="utf-8"
    )

    # Write report.md
    report_md = _matrix_to_report(
        matrix,
        structure_log=structure_log.relative_to(project_root)
        if structure_log.is_relative_to(project_root)
        else structure_log,
        results_count=len(results_paths),
        skipped_no_outcome=skipped_no_outcome,
        by_instrument_coverage=dict(by_instrument_coverage),
        by_instrument_regime_n=dict(by_instrument_regime_n),
        h4_rows_indexed=regime_index.h4_rows_indexed,
        h4_rows_skipped_no_symbol=regime_index.h4_rows_skipped_no_symbol,
    )
    (output_dir / "report.md").write_text(report_md, encoding="utf-8")

    # Console summary (compact)
    summary = matrix.summary()
    print(
        f"A5 regime matrix written to {output_dir}\n"
        f"  CANDs total: {matrix.total_cands}\n"
        f"  UNTAGGED: {matrix.untagged_count} "
        f"({_format_pct(summary['untagged_fraction'])})\n"
        f"  Best regime: {summary['best_regime']} "
        f"(avg WR {_format_pct(summary['best_avg_wr'])})\n"
        f"  Worst regime: {summary['worst_regime']} "
        f"(avg WR {_format_pct(summary['worst_avg_wr'])})\n"
        f"  WR delta: {summary['wr_delta_pp'] or 0.0:.1f}pp"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover — exercised via CLI
    raise SystemExit(main())
