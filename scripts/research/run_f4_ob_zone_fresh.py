"""F4 — Fresh OB-zone Test A re-test on H2-2026 data (CLI driver).

Drives :mod:`src.research_infra.ob_zone_test` over freshly-extracted BOS
events from H1 OHLCV (no cached inputs), running the canonical Test A Q2
comparison ("OB retest vs 50% Fibonacci pullback baseline") on the
2026-01-01 → 2026-04-24 window.

Outputs three artefacts under ``--output-dir``:
  - ``population.jsonl`` — one row per BOS event with both strategy
    outcomes side-by-side.
  - ``results.json`` — TestAReport (machine-readable verdict block).
  - ``report.md`` — human-readable strategic verdict.

Phase 1 = $0 API. This script makes NO Anthropic / OpenRouter calls.

Usage
-----
Default full-instrument fresh re-test::

    python scripts/research/run_f4_ob_zone_fresh.py \\
        --output-dir research/edge_decomposition/F4_ob_zone_fresh_test_a

Filtered::

    python scripts/research/run_f4_ob_zone_fresh.py \\
        --output-dir /tmp/scratch \\
        --start 2026-03-01 --end 2026-04-24 \\
        --instruments XAUUSD,GBPUSD

Dry-run (no writes; prints plan; exits 0)::

    python scripts/research/run_f4_ob_zone_fresh.py \\
        --output-dir /tmp/scratch --dry-run

Environment / .env note
=======================
This script does NOT read any environment variable (no API keys required).
Run directly from the repo root::

    python scripts/research/run_f4_ob_zone_fresh.py --output-dir <dir>
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import math
import sys
from pathlib import Path

# Make the project root importable when invoked as a file
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.ob_zone_test import (  # noqa: E402
    DEFAULT_FAMILY_SIZE,
    H1_2026_END,
    HARNESS_VERSION,
    TestAReport,
    run_test_a_fresh,
    serialize_population,
    serialize_report,
)


DEFAULT_OUTPUT_DIR = (
    _PROJECT_ROOT / "research" / "edge_decomposition"
    / "F4_ob_zone_fresh_test_a"
)
DEFAULT_OHLCV_DIR = _PROJECT_ROOT / "data" / "historical_2026"

DEFAULT_INSTRUMENTS = (
    "XAUUSD", "GBPUSD", "USDJPY", "GBPJPY",
    "US30_cash", "XAGUSD", "NAS100",
)

DEFAULT_START = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
DEFAULT_END = dt.datetime(2026, 4, 24, 23, 59, tzinfo=dt.timezone.utc)


def _parse_date(s: str) -> dt.datetime:
    parsed = dt.datetime.strptime(s, "%Y-%m-%d")
    return parsed.replace(tzinfo=dt.timezone.utc)


def _parse_instruments(s: str) -> list[str]:
    return [p.strip() for p in s.split(",") if p.strip()]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_f4_ob_zone_fresh",
        description=(
            "F4 — Fresh OB-zone Test A re-test. Re-derives BOS events from "
            "raw H1 OHLCV (no cached inputs) and re-runs the OB-retest vs "
            "50% Fibonacci pullback comparison on the 2026 window."
        ),
    )
    p.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help=(
            "Output directory for population.jsonl + results.json + "
            f"report.md. Default: {DEFAULT_OUTPUT_DIR}"
        ),
    )
    p.add_argument(
        "--ohlcv-dir", type=Path, default=DEFAULT_OHLCV_DIR,
        help=f"OHLCV directory. Default: {DEFAULT_OHLCV_DIR}",
    )
    p.add_argument(
        "--instruments", type=_parse_instruments,
        default=list(DEFAULT_INSTRUMENTS),
        help=(
            "Comma-separated instruments to include. "
            f"Default: {','.join(DEFAULT_INSTRUMENTS)}."
        ),
    )
    p.add_argument(
        "--start", type=_parse_date, default=DEFAULT_START,
        help="Start date (YYYY-MM-DD). Default: 2026-01-01.",
    )
    p.add_argument(
        "--end", type=_parse_date, default=DEFAULT_END,
        help="End date (YYYY-MM-DD). Default: 2026-04-24.",
    )
    p.add_argument(
        "--family-size", type=int, default=DEFAULT_FAMILY_SIZE,
        help=(
            "Bonferroni family size for corrected p. Default: "
            f"{DEFAULT_FAMILY_SIZE} (matches K52 canonical 5)."
        ),
    )
    p.add_argument(
        "--n-min", type=int, default=30,
        help="Minimum resolved trades per arm for SURVIVES_FRESH. Default: 30.",
    )
    p.add_argument(
        "--delta-floor-pp", type=float, default=5.0,
        help="Minimum (ob_wr - gen_wr) in pp for SURVIVES_FRESH. Default: 5.0.",
    )
    p.add_argument(
        "--alpha", type=float, default=0.05,
        help="Significance threshold on corrected p. Default: 0.05.",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Print plan; write nothing; exit 0.",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose progress logging.",
    )
    return p


def _format_p(p: float | None) -> str:
    if p is None:
        return "—"
    if isinstance(p, float) and not math.isfinite(p):
        return "—"
    if p < 1e-4:
        return f"{p:.2e}"
    return f"{p:.4f}"


def _format_pct(x: float | None) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    return f"{x * 100.0:.2f}%"


def _format_pp(x: float | None) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:.1f}pp"


def _strategic_verdict_block(report: TestAReport) -> list[str]:
    """Build the verdict block exactly as the F4 brief requires."""
    lines: list[str] = []
    lines.append("## Fresh OB-zone Test A (H2-2026 data, post-7d48001 main)")
    lines.append("")
    lines.append("| Period | n_bos | OB retest WR | Generic pullback WR | Δpp | corrected p |")
    lines.append("|---|---|---|---|---|---|")

    def _row(period: dict, label: str) -> str:
        return (
            f"| {label} "
            f"| {period['n_bos']} "
            f"| {_format_pct(period['ob_wr'])} ({period['ob_wins']}/{period['ob_resolved']}) "
            f"| {_format_pct(period['gen_wr'])} ({period['gen_wins']}/{period['gen_resolved']}) "
            f"| {_format_pp(period['delta_pp'])} "
            f"| {_format_p(period['corrected_p'])} |"
        )

    lines.append(_row(report.period_full, "Full"))
    lines.append(_row(report.period_h1, "H1-2026 only"))
    lines.append(_row(report.period_h2, "H2-2026 only"))
    lines.append("")

    lines.append("## Strategic verdict")
    lines.append("")
    lines.append("- Original Test A: +17pp (corrected p=0.003, n=219)")
    lines.append("- K52 cached re-test: +16.8pp (corrected p=0.0116, n=309 — SAME population as Test A)")

    h2 = report.period_h2
    n_total_h2 = h2["ob_resolved"] + h2["gen_resolved"]
    delta_str = _format_pp(h2["delta_pp"])
    p_str = _format_p(h2["corrected_p"])
    lines.append(
        f"- F4 fresh H2-2026: {delta_str} (corrected p={p_str}, "
        f"n={n_total_h2})"
    )
    lines.append(f"- Status: {h2['status']}")
    lines.append(f"- Reasoning: {_compose_reasoning(report)}")
    lines.append("")
    return lines


def _compose_reasoning(report: TestAReport) -> str:
    h2 = report.period_h2
    h1 = report.period_h1
    full = report.period_full

    if h2["status"] == "SURVIVES_FRESH":
        return (
            f"OB-zone advantage holds on freshly-extracted H2-2026 data with "
            f"delta = {_format_pp(h2['delta_pp'])} (corrected p = {_format_p(h2['corrected_p'])}, "
            f"n_ob={h2['ob_resolved']}, n_gen={h2['gen_resolved']}). "
            f"H1-2026 baseline delta = {_format_pp(h1['delta_pp'])}; "
            f"full-window delta = {_format_pp(full['delta_pp'])}. "
            f"K52's 'survives cached' verdict carries forward to fresh data — the "
            f"OB-zone signal is not an artefact of the original Test A population."
        )
    if h2["status"] == "DECAYED_FRESH":
        return (
            f"OB-zone advantage has DECAYED on freshly-extracted H2-2026 data: "
            f"delta = {_format_pp(h2['delta_pp'])} (corrected p = {_format_p(h2['corrected_p'])}, "
            f"n_ob={h2['ob_resolved']}, n_gen={h2['gen_resolved']}) — "
            f"either p-value is no longer significant under family size {report.family_size} "
            f"or the delta has dropped below the +{report.delta_floor_pp:g}pp floor. "
            f"H1-2026 baseline delta = {_format_pp(h1['delta_pp'])}; "
            f"full-window delta = {_format_pp(full['delta_pp'])}. "
            f"K52's cached SURVIVES verdict no longer holds on fresh H2 data — "
            f"the +17pp OB-zone advantage is sample-bound to the pre-2026 batch."
        )
    return (
        f"Insufficient H2-2026 sample for a verdict: n_ob={h2['ob_resolved']}, "
        f"n_gen={h2['gen_resolved']} (floor n_min={report.n_min_floor} per arm). "
        f"Cannot tell yet whether the OB-zone advantage has decayed. "
        f"Re-run as more data accumulates; full-window delta = "
        f"{_format_pp(full['delta_pp'])} (corrected p = {_format_p(full['corrected_p'])})."
    )


def _write_outputs(
    out_dir: Path,
    report: TestAReport,
    bos_events: list,
    ob_outcomes: list,
    gen_outcomes: list,
    args: argparse.Namespace,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # population.jsonl
    pop_path = out_dir / "population.jsonl"
    with pop_path.open("w", encoding="utf-8") as fh:
        for row in serialize_population(bos_events, ob_outcomes, gen_outcomes):
            from src.research_infra.ob_zone_test import _replace_nan  # noqa: WPS433
            fh.write(json.dumps(_replace_nan(row), default=str) + "\n")

    # results.json
    res_path = out_dir / "results.json"
    with res_path.open("w", encoding="utf-8") as fh:
        json.dump(serialize_report(report), fh, indent=2, default=str)

    # report.md
    rep_path = out_dir / "report.md"
    rep_path.write_text(_compose_report_md(report, args), encoding="utf-8")


def _compose_report_md(report: TestAReport, args: argparse.Namespace) -> str:
    lines: list[str] = []
    lines.append("# F4 — Fresh OB-zone Test A Re-test (H2-2026 Data)")
    lines.append("")
    lines.append(f"_Generated: {report.generated_at}_")
    lines.append(f"_Harness: {report.harness_version}_")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(
        "K52 (commit `7a68d1b`, 2026-04-26) re-tested the +17pp OB-zone "
        "advantage finding from CLAUDE.md but reused the **cached** Test A "
        "inputs (n=219 BOS events from a 2024-04 → 2026-03 batch). The "
        "corrected p remained 0.0116 — but the population was unchanged. "
        "F4 closes that gap by re-deriving the BOS-event population fresh "
        "from raw H1 OHLCV on the H2-2026 decay window and re-running the "
        "Q2 comparison."
    )
    lines.append("")

    # Verdict block
    lines.extend(_strategic_verdict_block(report))

    # Per-period detail
    lines.append("## Per-period detail")
    lines.append("")
    for period_key, period in (
        ("Full window", report.period_full),
        ("H1-2026", report.period_h1),
        ("H2-2026", report.period_h2),
    ):
        lines.append(f"### {period_key} — {period['status']}")
        lines.append("")
        lines.append(f"- BOS events: {period['n_bos']}")
        lines.append(
            f"- OB retest: {period['ob_wins']} / {period['ob_resolved']} = "
            f"{_format_pct(period['ob_wr'])} (filled = {period['ob_filled']})"
        )
        lines.append(
            f"- Generic 50% pullback: {period['gen_wins']} / {period['gen_resolved']} = "
            f"{_format_pct(period['gen_wr'])} (filled = {period['gen_filled']})"
        )
        lines.append(f"- Delta: {_format_pp(period['delta_pp'])}")
        lines.append(
            f"- Raw p = {_format_p(period['raw_p'])}; corrected p = "
            f"{_format_p(period['corrected_p'])} (Bonferroni × {report.family_size})"
        )
        lines.append(f"- Notes: {period['notes']}")
        lines.append("")

    # Per-instrument
    lines.append("## Per-instrument detail (full window)")
    lines.append("")
    lines.append("| Instrument | n_bos | OB WR | Generic WR | Δpp | corrected p | Status |")
    lines.append("|---|---|---|---|---|---|---|")
    for sym, p in report.per_instrument.items():
        lines.append(
            f"| {sym} | {p['n_bos']} "
            f"| {_format_pct(p['ob_wr'])} ({p['ob_wins']}/{p['ob_resolved']}) "
            f"| {_format_pct(p['gen_wr'])} ({p['gen_wins']}/{p['gen_resolved']}) "
            f"| {_format_pp(p['delta_pp'])} "
            f"| {_format_p(p['corrected_p'])} | {p['status']} |"
        )
    lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "**BOS detection** (per instrument H1 OHLCV; mirrors "
        "`src/components/market_state.py`):"
    )
    lines.append("")
    lines.append(
        f"- Swings: fractal high/low requiring strict dominance over "
        f"{2} bars on each side."
    )
    lines.append(
        f"- Structure direction: rolling classifier on the most-recent "
        f"{4} swings (HH+HL vs LH+LL net score)."
    )
    lines.append(
        "- BOS event: candle close exceeds the most-recent swing in the "
        "structural direction. Each swing level consumed at most once."
    )
    lines.append("")
    lines.append("**OB retest entry** (canonical 80% retrace into OB):")
    lines.append("")
    lines.append(
        "- OB = last opposing-side candle within 10 bars before the BOS "
        "(mirrors production `identify_order_blocks`)."
    )
    lines.append(
        "- Entry = OB.low + 0.80 × (OB.high - OB.low) for LONG; "
        "OB.high - 0.80 × (OB.high - OB.low) for SHORT."
    )
    lines.append(
        "- SL buffer = max(0.25 × ATR_14, 5 × tick_size); SL = "
        "OB.low - buffer (LONG) / OB.high + buffer (SHORT)."
    )
    lines.append("- TP = entry ± 1.5 × |entry - SL| (min_rr floor).")
    lines.append("")
    lines.append("**Generic pullback entry** (50% Fibonacci retrace):")
    lines.append("")
    lines.append(
        "- Entry = anchor swing price + 0.50 × (BOS close - anchor) for "
        "LONG; anchor + 0.50 × (BOS close - anchor) for SHORT (signed)."
    )
    lines.append(
        "- SL = anchor swing price - buffer (LONG) / + buffer (SHORT). "
        "SL beyond the impulse origin matches the 'generic deep "
        "pullback' interpretation."
    )
    lines.append("- TP = entry ± 1.5 × |entry - SL|.")
    lines.append("")
    lines.append(
        "**Outcome resolution**: walk-forward on M15 OHLCV via "
        "`src.research_infra.dumb_baseline.resolve_mechanical_outcome`. "
        "Two-stage walk: wait for fill (limit-order semantics), then "
        "watch for TP/SL with SL-first conservative rule. Same-bar "
        "fill+TP/SL excluded as ambiguous (no microstructure)."
    )
    lines.append("")
    lines.append(
        f"**Statistical test**: pooled-variance two-proportion z-test "
        f"on (OB_wins / OB_resolved) vs (Generic_wins / Generic_resolved). "
        f"Bonferroni at family size {report.family_size}."
    )
    lines.append("")
    lines.append("**Status decision rule**:")
    lines.append("")
    lines.append(
        f"- `SURVIVES_FRESH` — corrected p < α = {report.alpha} AND "
        f"delta_pp ≥ +{report.delta_floor_pp:g}pp on H2-2026 (n_min "
        f"per arm ≥ {report.n_min_floor})."
    )
    lines.append(
        f"- `DECAYED_FRESH` — corrected p ≥ α OR delta_pp < "
        f"+{report.delta_floor_pp:g}pp."
    )
    lines.append(
        f"- `INCONCLUSIVE_FRESH_SAMPLE` — n < n_min on H2-2026."
    )
    lines.append("")

    # Caveats
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "- **Different test from original Test A.** The original Test A "
        "(2024) used Fisher exact on a pre-AI sample. F4 uses pooled-z "
        "for direct K52 comparability; Fisher exact and pooled-z agree "
        "well at n > 30 but can disagree on small samples."
    )
    lines.append(
        "- **Different baseline geometry.** The original Test A "
        "(`.context/03_analysis/test_a_rerun_real_bos_results.md`) tested "
        "OB vs 80% retrace of the *impulse range estimated from entry / "
        "SL / Fibonacci %*. F4 tests OB vs 50% Fibonacci retracement of "
        "the *swing-anchor → BOS close* impulse — a more standard SMC "
        "definition. The 50% level is arithmetically deeper than 80% on "
        "the impulse range (because 80% retrace = 20% remaining = a "
        "shallower entry from the impulse origin); the 'generic deep "
        "pullback' framing is preserved."
    )
    lines.append(
        "- **No simulation calibration.** The original Test A reported a "
        "+12.6pp simulation gap (real WR < sim WR by ~13pp). F4 does not "
        "calibrate against AI-selected real fills because it tests a "
        "DIFFERENT comparison (OB vs generic pullback, both mechanical), "
        "where the calibration cancels."
    )
    lines.append(
        "- **n=309 in K52 cached vs F4 fresh n.** K52's n=309 came from "
        "the per-record OB structural backtest, not a re-extracted "
        "BOS-event tally. F4's n is the freshly-derived BOS count; "
        "compare to the original Test A n=219 (closer to the same "
        "geometry)."
    )
    lines.append(
        "- **No realised-AI-R join.** F4 is mechanical-vs-mechanical "
        "(OB vs generic) — same as the original Test A Q2. The "
        "AI-vs-mechanical comparison lives in A1 dumb_baseline / B12 / "
        "K50; do not conflate."
    )
    lines.append(
        f"- **Family size {report.family_size} is the K52 canonical.** "
        f"F4's corrected p uses the same divisor so the verdict slots "
        f"into the K52 narrative directly."
    )
    lines.append(
        f"- **Period split: Jan-Feb 2026 = H1; Mar-Apr 2026 = H2.** "
        f"Matches CLAUDE.md unresolved item #4 (XAUUSD H1→H2 2026 WR "
        f"decay framing). H1_2026_END = {H1_2026_END.date().isoformat()}."
    )
    lines.append("")

    # Args echo
    lines.append("## Run parameters")
    lines.append("")
    lines.append(f"- Output: `{args.output_dir}`")
    lines.append(f"- OHLCV: `{args.ohlcv_dir}`")
    lines.append(f"- Instruments: {','.join(report.instruments)}")
    lines.append(f"- Window: {report.start_date} → {report.end_date}")
    lines.append(f"- Family size: {report.family_size}")
    lines.append(f"- α = {report.alpha}")
    lines.append(f"- n_min (per arm): {report.n_min_floor}")
    lines.append(f"- Δpp floor: +{report.delta_floor_pp:g}pp")
    lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log = logging.getLogger("run_f4_ob_zone_fresh")

    log.info("F4 fresh OB-zone Test A re-test (harness %s)", HARNESS_VERSION)
    log.info("  Output:      %s", args.output_dir)
    log.info("  OHLCV:       %s", args.ohlcv_dir)
    log.info("  Instruments: %s", ",".join(args.instruments))
    log.info("  Window:      %s → %s",
             args.start.date().isoformat(), args.end.date().isoformat())
    log.info("  Family size: %d", args.family_size)
    log.info("  α / n_min / delta_floor: %.3f / %d / +%.1fpp",
             args.alpha, args.n_min, args.delta_floor_pp)

    if args.dry_run:
        log.info("DRY RUN — no writes; exiting 0.")
        return 0

    if not args.ohlcv_dir.exists():
        log.error("OHLCV dir missing: %s", args.ohlcv_dir)
        return 2

    progress = log.info if args.verbose else (lambda _: None)

    report, bos_events, ob_outcomes, gen_outcomes = run_test_a_fresh(
        start_date=args.start,
        end_date=args.end,
        instruments=args.instruments,
        ohlcv_dir=args.ohlcv_dir,
        family_size=args.family_size,
        n_min=args.n_min,
        delta_floor_pp=args.delta_floor_pp,
        alpha=args.alpha,
        progress=progress,
    )

    log.info(
        "Extracted %d BOS events; full-window delta = %.2fpp, corrected p = %s",
        report.n_bos_total,
        report.period_full["delta_pp"]
        if math.isfinite(report.period_full["delta_pp"]) else float("nan"),
        report.period_full["corrected_p"],
    )

    _write_outputs(args.output_dir, report, bos_events, ob_outcomes,
                   gen_outcomes, args)
    log.info(
        "Wrote: %s, %s, %s",
        args.output_dir / "population.jsonl",
        args.output_dir / "results.json",
        args.output_dir / "report.md",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
