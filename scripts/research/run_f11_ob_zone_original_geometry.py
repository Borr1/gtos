"""F11 — OB-zone advantage with ORIGINAL Test A geometry (CLI driver).

Drives :mod:`src.research_infra.ob_zone_original_geometry` to disambiguate
F4's ``DECAYED_FRESH`` verdict (delta = +0.9pp on H2-2026, n=480) versus
the original Test A's +17pp finding (n=219, Fisher p=0.003).

By default, F11 loads BOS events from F4's ``population.jsonl`` so the
SAME population is scored under different baseline geometry — the only
difference is methodology. If F4's file is missing or
``--no-use-f4-population`` is passed, F11 re-extracts BOS events fresh
with the same parameters as F4.

Outputs three artefacts under ``--output-dir``:
  - ``population.jsonl`` — one row per BOS pairing OB retest +
    original-geometry baseline.
  - ``results.json`` — F11Report (machine-readable verdict block).
  - ``report.md`` — methodology comparison + verdict interpretation.

Phase 1 = $0 API. NO Anthropic / OpenRouter calls.

Usage
-----
Default (paired comparison on F4's saved population)::

    python scripts/research/run_f11_ob_zone_original_geometry.py \
        --output-dir research/edge_decomposition/F11_ob_zone_original_geometry

Filtered::

    python scripts/research/run_f11_ob_zone_original_geometry.py \
        --output-dir /tmp/f11 \
        --start 2026-03-01 --end 2026-04-24 \
        --instruments XAUUSD,GBPUSD

Force fresh extract (no F4 population reuse)::

    python scripts/research/run_f11_ob_zone_original_geometry.py \
        --output-dir /tmp/f11 --no-use-f4-population

Dry-run::

    python scripts/research/run_f11_ob_zone_original_geometry.py \
        --output-dir /tmp/scratch --dry-run
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

from src.research_infra.ob_zone_original_geometry import (  # noqa: E402
    DEFAULT_FAMILY_SIZE,
    DEFAULT_OUTPUT_DIR,
    F11Report,
    HARNESS_VERSION,
    H1_2026_END,
    F4_POPULATION_PATH,
    run_f11_original_geometry,
    serialize_population,
    serialize_report,
)
from src.research_infra.ob_zone_test import _replace_nan  # noqa: E402


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
        prog="run_f11_ob_zone_original_geometry",
        description=(
            "F11 — re-run F4's OB-zone test on the same fresh population "
            "but using the ORIGINAL Test A's 80%-of-impulse-range retrace "
            "baseline + Fisher exact. Disambiguates F4's DECAYED_FRESH "
            "verdict (real decay vs methodology drift)."
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
        "--f4-population-path", type=Path, default=F4_POPULATION_PATH,
        help=(
            "Path to F4's population.jsonl. F11 reads this to score the SAME "
            f"BOS events under different geometry. Default: {F4_POPULATION_PATH}"
        ),
    )
    p.add_argument(
        "--no-use-f4-population", action="store_true",
        help=(
            "Skip F4 population reuse and re-extract BOS events fresh from "
            "H1 OHLCV. Default: use F4 if available."
        ),
    )
    p.add_argument(
        "--instruments", type=_parse_instruments,
        default=list(DEFAULT_INSTRUMENTS),
        help=(
            "Comma-separated instruments. "
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
            f"Bonferroni family size. Default: {DEFAULT_FAMILY_SIZE} "
            "(matches K52 / F4 canonical)."
        ),
    )
    p.add_argument(
        "--n-min", type=int, default=30,
        help="Minimum resolved trades per arm for a verdict. Default: 30.",
    )
    p.add_argument(
        "--delta-confirmed-floor", type=float, default=12.0,
        help=(
            "Min delta_pp for CONFIRMED verdict (close to original "
            "Test A +17pp). Default: 12.0pp."
        ),
    )
    p.add_argument(
        "--delta-partial-floor", type=float, default=5.0,
        help=(
            "Min |delta_pp| for PARTIAL verdict; below this threshold "
            "F11 emits METHODOLOGY_DRIFT (close to F4's +0.9pp). "
            "Default: 5.0pp."
        ),
    )
    p.add_argument(
        "--delta-partial-ceiling", type=float, default=12.0,
        help=(
            "Upper bound of PARTIAL verdict band. Above → CONFIRMED. "
            "Default: 12.0pp."
        ),
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


def _verdict_table(report: F11Report) -> list[str]:
    """Build the canonical methodology-comparison table.

    Columns: Method, Baseline, Test, n_paired, OB WR, Baseline WR,
    Δpp, p (raw), p (corrected). Matches the brief's verdict format.
    """
    lines: list[str] = []
    h2 = report.period_h2

    n_paired = h2.ob_resolved + h2.gen_resolved

    lines.append(
        "## OB-zone advantage on H2-2026: methodology comparison"
    )
    lines.append("")
    lines.append(
        "| Method | Baseline | Test | n_paired | OB WR | Baseline WR "
        "| Δpp | p (raw) | p (corrected) |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|---|"
    )
    # F4 published row (from F4's results.json on the same H2 period)
    lines.append(
        "| F4 published | 50% Fib retrace | pooled-z | 480 | 57.59% | "
        "56.64% | +0.9 | 0.8341 | 1.0000 |"
    )
    # F11 original geometry — Fisher
    lines.append(
        f"| F11 (original geometry) | 80% impulse retrace | Fisher | "
        f"{n_paired} | {_format_pct(h2.ob_wr)} | {_format_pct(h2.gen_wr)} | "
        f"{_format_pp(h2.delta_pp)} | {_format_p(h2.fisher_raw_p)} | "
        f"{_format_p(h2.fisher_corrected_p)} |"
    )
    # F11 original geometry — pooled z
    lines.append(
        f"| F11 (original geometry) | 80% impulse retrace | pooled-z | "
        f"{n_paired} | {_format_pct(h2.ob_wr)} | {_format_pct(h2.gen_wr)} | "
        f"{_format_pp(h2.delta_pp)} | {_format_p(h2.z_raw_p)} | "
        f"{_format_p(h2.z_corrected_p)} |"
    )
    # Original Test A row (cached numbers)
    lines.append(
        "| Original Test A | 80% impulse retrace | Fisher | 219 | 70.50% "
        "| 53.70% | +16.8 | 0.0029 | 0.0145 |"
    )
    lines.append("")
    return lines


def _verdict_block(report: F11Report) -> list[str]:
    """Build the strategic verdict block."""
    lines: list[str] = []
    h2 = report.period_h2
    full = report.period_full
    h1 = report.period_h1

    # F4 published H2 delta (canonical reference for the gap narrative)
    f4_h2_delta = 0.9486607142857095  # from F4 results.json
    original_delta = 16.8  # from .context/03_analysis/test_a_rerun_real_bos_results.md

    if math.isfinite(h2.delta_pp):
        methodology_shift = h2.delta_pp - f4_h2_delta
        decay_remaining = original_delta - h2.delta_pp
    else:
        methodology_shift = float("nan")
        decay_remaining = float("nan")

    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"- F4's \"DECAYED_FRESH\" verdict is: **{h2.verdict}**"
    )
    lines.append(f"- Reasoning: {h2.notes}")
    if math.isfinite(methodology_shift) and math.isfinite(decay_remaining):
        lines.append(
            f"- Decomposition: F4 H2 delta = +{f4_h2_delta:.1f}pp; "
            f"F11 H2 delta = {_format_pp(h2.delta_pp)}; original Test A = "
            f"+{original_delta:.1f}pp."
        )
        lines.append(
            f"  - Methodology shift (F11 − F4) = "
            f"{_format_pp(methodology_shift)}"
        )
        lines.append(
            f"  - Residual decay (original − F11) = "
            f"{_format_pp(decay_remaining)}"
        )
    lines.append("")
    lines.append("## Strategic implication")
    lines.append("")
    if h2.verdict == "CONFIRMED":
        impl = (
            "Restoring the original Test A baseline geometry recovers an "
            "OB-zone advantage on H2-2026 data comparable to the canonical "
            "+17pp finding. F4's DECAYED_FRESH verdict was driven primarily "
            "by methodology drift (50% Fib midpoint baseline + pooled-z) — "
            "NOT by genuine decay of the OB-zone signal. The +17pp Validated "
            "Number remains defensible on the H2-2026 population when "
            "measured against the original-Test-A deep-pullback baseline. "
            "Update CLAUDE.md to flag the methodology sensitivity but "
            "RETAIN the OB-zone advantage as live."
        )
    elif h2.verdict == "METHODOLOGY_DRIFT":
        # Differentiate "pure decay" from "decay-dominant + methodology contributes"
        if math.isfinite(methodology_shift) and methodology_shift >= 2.0:
            impl = (
                f"Restoring the original Test A baseline geometry "
                f"shifted the H2-2026 delta from F4's +{f4_h2_delta:.1f}pp "
                f"to {_format_pp(h2.delta_pp)} — methodology DID "
                f"contribute ({_format_pp(methodology_shift)}), but the "
                f"residual gap to the original +{original_delta:.1f}pp "
                f"({_format_pp(decay_remaining)}) is real decay. Both "
                f"effects are present, but DECAY DOMINATES — the OB-zone "
                f"advantage on H2-2026 data is materially smaller than "
                f"the original +17pp regardless of methodology. Move the "
                f"+17pp Validated Number to a 'historical / decayed on "
                f"H2-2026' footnote with the methodology caveat; keep K52 "
                f"SURVIVES tied to the pre-2026 sample."
            )
        else:
            impl = (
                "Restoring the original Test A baseline geometry did NOT "
                "recover the +17pp advantage on H2-2026 data — both Fisher "
                "exact and pooled-z agree that the OB-zone advantage has "
                "DECAYED (or reversed) on the current population, "
                "regardless of baseline choice. F4's DECAYED_FRESH is real "
                "decay, not methodology drift. The original +17pp finding "
                "should be moved to a 'historical / decayed on H2-2026' "
                "footnote in Validated Numbers; keep the cached K52 "
                "SURVIVES verdict tied to the pre-2026 sample."
            )
    elif h2.verdict == "PARTIAL":
        impl = (
            "Restoring the original Test A baseline geometry partially "
            "recovers the OB-zone advantage on H2-2026 data — the delta "
            "moves from F4's +0.9pp toward the original +17pp but does "
            "not reach significance under the K52 family-size correction. "
            "BOTH effects contribute: F4's methodology drift understated "
            "the advantage, AND genuine decay has shrunk it from the "
            "original +17pp baseline. Keep CLAUDE.md Validated Number "
            "with a 'decay-in-progress, n-limited' caveat; re-run F11 "
            "quarterly as more data accumulates."
        )
    else:  # INCONCLUSIVE_FRESH_SAMPLE
        impl = (
            "Insufficient H2-2026 sample for a verdict — re-run F11 as "
            "more data accumulates. The methodology comparison itself is "
            "methodologically sound; the limitation is sample size."
        )
    lines.append(f"- {impl}")
    lines.append("")
    lines.append("## Cross-period context")
    lines.append("")
    lines.append(
        f"- Full window: delta = {_format_pp(full.delta_pp)} "
        f"(Fisher corrected p = {_format_p(full.fisher_corrected_p)}, "
        f"z corrected p = {_format_p(full.z_corrected_p)})"
    )
    lines.append(
        f"- H1-2026: delta = {_format_pp(h1.delta_pp)} "
        f"(Fisher corrected p = {_format_p(h1.fisher_corrected_p)}, "
        f"z corrected p = {_format_p(h1.z_corrected_p)})"
    )
    lines.append(
        f"- H2-2026: delta = {_format_pp(h2.delta_pp)} "
        f"(Fisher corrected p = {_format_p(h2.fisher_corrected_p)}, "
        f"z corrected p = {_format_p(h2.z_corrected_p)})"
    )
    lines.append("")
    return lines


def _per_period_detail(report: F11Report) -> list[str]:
    lines: list[str] = []
    lines.append("## Per-period detail")
    lines.append("")

    for label, period in (
        ("Full window", report.period_full),
        ("H1-2026", report.period_h1),
        ("H2-2026", report.period_h2),
    ):
        lines.append(f"### {label} — {period.verdict}")
        lines.append("")
        lines.append(f"- BOS events: {period.n_bos}")
        lines.append(
            f"- OB retest: {period.ob_wins} / {period.ob_resolved} = "
            f"{_format_pct(period.ob_wr)} (filled = {period.ob_filled})"
        )
        lines.append(
            f"- Original-80%-origin baseline: {period.gen_wins} / "
            f"{period.gen_resolved} = {_format_pct(period.gen_wr)} "
            f"(filled = {period.gen_filled})"
        )
        lines.append(f"- Delta: {_format_pp(period.delta_pp)}")
        lines.append(
            f"- Fisher exact: raw p = {_format_p(period.fisher_raw_p)}, "
            f"corrected p = {_format_p(period.fisher_corrected_p)} "
            f"(× {report.family_size})"
        )
        lines.append(
            f"- Pooled-z: raw p = {_format_p(period.z_raw_p)}, "
            f"corrected p = {_format_p(period.z_corrected_p)} "
            f"(× {report.family_size})"
        )
        lines.append(f"- Notes: {period.notes}")
        lines.append("")
    return lines


def _per_instrument_detail(report: F11Report) -> list[str]:
    lines: list[str] = []
    lines.append("## Per-instrument detail (full window)")
    lines.append("")
    lines.append(
        "| Instrument | n_bos | OB WR | Baseline WR | Δpp | Fisher p | "
        "z p | Verdict |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|"
    )
    for sym, p in report.per_instrument.items():
        lines.append(
            f"| {sym} | {p.n_bos} "
            f"| {_format_pct(p.ob_wr)} ({p.ob_wins}/{p.ob_resolved}) "
            f"| {_format_pct(p.gen_wr)} ({p.gen_wins}/{p.gen_resolved}) "
            f"| {_format_pp(p.delta_pp)} "
            f"| {_format_p(p.fisher_corrected_p)} "
            f"| {_format_p(p.z_corrected_p)} | {p.verdict} |"
        )
    lines.append("")
    return lines


def _methodology(report: F11Report) -> list[str]:
    lines: list[str] = []
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        f"**Population source**: `{report.population_source}` "
        + (
            f"(loaded {report.n_bos_total} BOS from "
            f"`{report.population_path}`)"
            if report.population_source == "f4_jsonl"
            else f"(re-extracted {report.n_bos_total} BOS fresh from H1 OHLCV)"
        )
    )
    lines.append("")
    lines.append("**OB retest entry** (identical to F4):")
    lines.append("")
    lines.append(
        "- OB = last opposing-side candle within 10 bars before BOS."
    )
    lines.append(
        "- Entry = `OB.low + 0.80 × (OB.high - OB.low)` for LONG; mirrored "
        "for SHORT."
    )
    lines.append(
        "- SL = beyond the OB extreme by `max(0.25 × ATR_14, 5 × tick_size)`."
    )
    lines.append("- TP = `entry + 1.5 × |entry - SL|`.")
    lines.append("")
    lines.append("**Original-geometry baseline entry** (the F11 contribution):")
    lines.append("")
    lines.append(
        "- Anchor = swing low (LONG) or swing high (SHORT) before the BOS."
    )
    lines.append(
        "- Impulse range = `bos_close - anchor_swing_price` (signed)."
    )
    lines.append(
        "- Entry = `anchor + (1 - 0.80) × impulse_range = anchor + 0.20 × "
        "impulse_range` — i.e. **80% retracement back from BOS close toward "
        "the anchor swing**, equivalent to a 20%-from-anchor entry. This "
        "matches the original Test A "
        "(`.context/03_analysis/test_a_rerun_real_bos_results.md` Q2)."
    )
    lines.append(
        "- SL = beyond the anchor swing extreme by the same buffer "
        "formula as F4's `generic_50pct` arm."
    )
    lines.append("- TP = `entry ± 1.5 × |entry - SL|`.")
    lines.append("")
    lines.append("**Geometric note**: F4 used a 50%-Fibonacci entry "
                 "(`anchor + 0.50 × impulse_range`); F11 uses a 20%-of-range entry "
                 "(`anchor + 0.20 × impulse_range`). F11's entry is therefore "
                 "**closer to the impulse origin** (deeper pullback) — this is "
                 "the geometry that produced the original +17pp finding "
                 "and is the geometry F4 implicitly drifted away from.")
    lines.append("")
    lines.append("**Outcome resolution**: walk-forward on M15 OHLCV via "
                 "`src.research_infra.dumb_baseline.resolve_mechanical_outcome` "
                 "— bit-identical semantics to F4. Two-stage walk: limit-order "
                 "fill then TP/SL with SL-first conservative rule. Hard 24h "
                 "hold ceiling (96 M15 bars).")
    lines.append("")
    lines.append("**Statistical tests**:")
    lines.append("")
    lines.append(
        f"- **Fisher exact** (matches original Test A): pure-Python two-tailed "
        f"hypergeometric tail enumeration, no scipy dependency. "
        f"Bonferroni × {report.family_size}."
    )
    lines.append(
        f"- **Pooled-variance two-proportion z-test** (matches K52 / F4): "
        f"identical implementation. Bonferroni × {report.family_size}."
    )
    lines.append("")
    lines.append("**Verdict decision rule** (applied to H2-2026 row):")
    lines.append("")
    lines.append(
        f"- **CONFIRMED** — delta_pp ≥ +{report.delta_pp_partial_ceiling:g}pp "
        f"AND ≥ 1 corrected p < α = {report.alpha}."
    )
    lines.append(
        f"- **PARTIAL** — delta_pp ∈ [+{report.delta_pp_partial_floor:g}pp, "
        f"+{report.delta_pp_partial_ceiling:g}pp); methodology + decay both "
        f"contribute."
    )
    lines.append(
        f"- **METHODOLOGY_DRIFT** — |delta_pp| < {report.delta_pp_partial_floor:g}pp "
        f"AND no corrected p < α; F4's DECAYED_FRESH is real decay."
    )
    lines.append(
        f"- **INCONCLUSIVE_FRESH_SAMPLE** — n_resolved < {report.n_min_floor} "
        f"per arm."
    )
    lines.append("")
    return lines


def _caveats(report: F11Report) -> list[str]:
    lines: list[str] = []
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "- **Same population guarantee.** When loaded from F4's "
        "`population.jsonl` (the default path), F11 scores the SAME "
        "BOS events F4 scored — only the baseline geometry and "
        "statistical test differ. This isolates methodology drift "
        "as the explanatory variable."
    )
    lines.append(
        "- **F4 OB-retest counts may differ trivially.** F4 logged "
        "OB-retest outcomes; F11 re-resolves them via the same code path "
        "(`find_ob_retest_outcome`). On the same population the counts "
        "are bit-identical; we re-run them to keep F11 self-contained."
    )
    lines.append(
        "- **Fisher exact symmetry convention.** This implementation "
        "uses the symmetric-around-mean two-tailed convention "
        "(matching `scipy.stats.fisher_exact(alternative='two-sided')`). "
        "Verified against scipy on (122/173, 73/136), (50/100, 50/100), "
        "and (8/10, 1/10) — exact agreement to 6 decimal places."
    )
    lines.append(
        "- **Bonferroni family size.** F11 uses the K52-canonical "
        f"family size of {report.family_size} so corrected p is directly "
        "comparable to K52's SURVIVES verdict and F4's DECAYED_FRESH."
    )
    lines.append(
        "- **Geometry stricter than F4 baseline.** F11's entry "
        "(`anchor + 0.20 × impulse_range`) sits closer to the impulse "
        "origin than F4's (`anchor + 0.50 × impulse_range`). The original "
        "Test A's 80%-retrace baseline is THIS deeper level — F11 "
        "restores it. A `CONFIRMED` verdict here is a strong recovery of "
        "the original advantage."
    )
    lines.append(
        f"- **Period split: H1_2026_END = "
        f"{H1_2026_END.date().isoformat()}.** Matches F4 + CLAUDE.md "
        "unresolved item #4 (XAUUSD H1→H2 2026 WR decay framing)."
    )
    lines.append(
        "- **No simulation calibration.** Both arms use identical M15 "
        "walk-forward; calibration cancels in the delta. Same caveat as F4."
    )
    lines.append("")
    return lines


def _compose_report_md(report: F11Report, args: argparse.Namespace) -> str:
    lines: list[str] = []
    lines.append("# F11 — OB-zone Advantage Re-test with ORIGINAL Test A Geometry")
    lines.append("")
    lines.append(f"_Generated: {report.generated_at}_")
    lines.append(f"_Harness: {report.harness_version}_")
    lines.append("")

    lines.append("## Overview")
    lines.append("")
    lines.append(
        "F4 (`research/edge_decomposition/F4_ob_zone_fresh_test_a/`, commit "
        "`48395e2`) re-extracted BOS events fresh from H1 OHLCV and "
        "reported a **DECAYED_FRESH** verdict on H2-2026: delta = +0.9pp "
        "(corrected p = 1.0, n=480). That contrasts sharply with the "
        "original Test A's +17pp (Fisher p = 0.003, n=219 from "
        "`.context/03_analysis/test_a_rerun_real_bos_results.md`). F4 "
        "changed two things at once relative to the original:"
    )
    lines.append("")
    lines.append(
        "1. **Baseline geometry**: 50%-Fibonacci of `anchor → BOS close` "
        "(F4) vs 80%-of-impulse-range retrace from origin (original)."
    )
    lines.append(
        "2. **Statistical test**: pooled-z (F4, K52-comparable) vs Fisher "
        "exact (original Test A)."
    )
    lines.append("")
    lines.append(
        "F11 re-runs F4's analysis on the SAME freshly-extracted population "
        "but with the original Test A's baseline geometry (deeper, closer "
        "to the impulse origin) AND BOTH Fisher exact + pooled-z reported. "
        "This isolates methodology drift as the explanatory variable."
    )
    lines.append("")

    # The verdict table comes first (per the brief)
    lines.extend(_verdict_table(report))
    lines.extend(_verdict_block(report))
    lines.extend(_per_period_detail(report))
    lines.extend(_per_instrument_detail(report))
    lines.extend(_methodology(report))
    lines.extend(_caveats(report))

    # Args echo
    lines.append("## Run parameters")
    lines.append("")
    lines.append(f"- Output: `{args.output_dir}`")
    lines.append(f"- OHLCV: `{args.ohlcv_dir}`")
    lines.append(f"- F4 population path: `{args.f4_population_path}`")
    lines.append(
        f"- Use F4 population: "
        f"{'no (forced fresh extract)' if args.no_use_f4_population else 'yes'}"
    )
    lines.append(f"- Instruments: {','.join(report.instruments)}")
    lines.append(f"- Window: {report.start_date} → {report.end_date}")
    lines.append(f"- Family size: {report.family_size}")
    lines.append(f"- α = {report.alpha}")
    lines.append(f"- n_min (per arm): {report.n_min_floor}")
    lines.append(
        f"- Δpp partial floor / ceiling: "
        f"+{report.delta_pp_partial_floor:g}pp / "
        f"+{report.delta_pp_partial_ceiling:g}pp"
    )
    lines.append("")

    return "\n".join(lines) + "\n"


def _write_outputs(
    out_dir: Path,
    report: F11Report,
    bos_events: list,
    ob_outcomes: list,
    f11_outcomes: list,
    args: argparse.Namespace,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # population.jsonl
    pop_path = out_dir / "population.jsonl"
    with pop_path.open("w", encoding="utf-8") as fh:
        for row in serialize_population(bos_events, ob_outcomes, f11_outcomes):
            fh.write(json.dumps(_replace_nan(row), default=str) + "\n")

    # results.json
    res_path = out_dir / "results.json"
    with res_path.open("w", encoding="utf-8") as fh:
        json.dump(serialize_report(report), fh, indent=2, default=str)

    # report.md
    rep_path = out_dir / "report.md"
    rep_path.write_text(_compose_report_md(report, args), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log = logging.getLogger("run_f11_ob_zone_original_geometry")

    log.info("F11 original-geometry re-test (harness %s)", HARNESS_VERSION)
    log.info("  Output:           %s", args.output_dir)
    log.info("  OHLCV:            %s", args.ohlcv_dir)
    log.info("  F4 population:    %s", args.f4_population_path)
    log.info("  Use F4 population: %s",
             "NO (fresh extract)" if args.no_use_f4_population else "YES")
    log.info("  Instruments:      %s", ",".join(args.instruments))
    log.info("  Window:           %s → %s",
             args.start.date().isoformat(), args.end.date().isoformat())
    log.info("  Family size:      %d", args.family_size)
    log.info("  α / n_min / partial floor / ceiling: "
             "%.3f / %d / +%.1fpp / +%.1fpp",
             args.alpha, args.n_min,
             args.delta_partial_floor, args.delta_partial_ceiling)

    if args.dry_run:
        log.info("DRY RUN — no writes; exiting 0.")
        return 0

    if not args.ohlcv_dir.exists():
        log.error("OHLCV dir missing: %s", args.ohlcv_dir)
        return 2

    progress = log.info if args.verbose else (lambda _: None)

    report, bos_events, ob_outcomes, f11_outcomes = run_f11_original_geometry(
        start_date=args.start,
        end_date=args.end,
        instruments=args.instruments,
        ohlcv_dir=args.ohlcv_dir,
        family_size=args.family_size,
        n_min=args.n_min,
        delta_confirmed_floor=args.delta_partial_ceiling,
        delta_partial_floor=args.delta_partial_floor,
        delta_partial_ceiling=args.delta_partial_ceiling,
        alpha=args.alpha,
        f4_population_path=args.f4_population_path,
        use_f4_population=not args.no_use_f4_population,
        progress=progress,
    )

    h2 = report.period_h2
    log.info(
        "Extracted %d BOS events; H2 delta = %.2fpp, "
        "Fisher corrected p = %s, z corrected p = %s, verdict = %s",
        report.n_bos_total,
        h2.delta_pp if math.isfinite(h2.delta_pp) else float("nan"),
        h2.fisher_corrected_p, h2.z_corrected_p, h2.verdict,
    )

    _write_outputs(
        args.output_dir, report, bos_events, ob_outcomes, f11_outcomes, args,
    )
    log.info(
        "Wrote: %s, %s, %s",
        args.output_dir / "population.jsonl",
        args.output_dir / "results.json",
        args.output_dir / "report.md",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
