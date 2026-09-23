"""F12 — US30 hallucination tolerance sweep (CLI driver).

Tests F9's H4 hypothesis (45-50-tick midpoint precision rounding) by
sweeping the price-match tolerance across ``[5, 10, 20, 50, 100]`` ticks
and tabulating how the per-classification status changes.

The downstream question
=======================
F9 (commit ``cffb99c``) found that 7 of 26 US30 trade_records share a
deterministic 45-50-tick offset between AI-cited ``ob_mid`` and the
true MSO-derived midpoint. F9 noted: "Re-run F9 with
``--tolerance-ticks 50`` to test H4 (precision rounding) directly. Out
of scope for this brief."

F12 fills that gap. It re-runs F9's analysis at each tolerance value
and audits which classification rows flip status (hallucinated /
misattributed → accurate, or vice versa).

If H4 is correct, the 7 ~45-50-tick-offset records flip from
``hallucinated`` to ``accurate`` at ``tolerance=50``, and the overall
US30 hallucination rate drops noticeably.

If H4 is wrong, those 7 records stay ``hallucinated`` even at the
widest tolerance — meaning the offsets are real grounding failures,
not precision rounding (the MSO simply does not contain the AI's
cited price).

Inputs (read-only)
==================
* ``knowledge_base/trade_records/US30_cash/*.json`` — same precise arm
  as F9.
* ``knowledge_base/live_evaluations/US30_cash/*.jsonl`` — same coarse
  arm as F9.
* B7 module ``src.research_infra.hallucination_measurement`` —
  consumed read-only via F9's ``run_deepdive``. Neither B7 nor F9 is
  modified.

Outputs (caller-supplied directory; defaults to
``research/ai_behavior/F12_us30_tolerance_sweep/``):

* ``sweep.json`` — full machine-readable sweep:
    - ``per_tolerance``: list of ``{tolerance_ticks, n_evaluations,
      n_prices, n_accurate, n_hallucinated, n_misattributed,
      hallucination_pct, n_records_flipping_vs_baseline}`` rows
    - ``flipping_records``: per-record audit of every classification
      whose status changed across tolerance values
    - ``baseline_tolerance``: 5 (anchor)
* ``flipping_records.jsonl`` — one line per flipped classification,
  schema documented in ``write_flipping_records_jsonl`` docstring.
* ``report.md`` — human-readable verdict block following the F12 spec.

Out of scope
============
* Modifying production code, prompts, or config.
* Modifying the F9 module/output or the B7 module/output.
* Proposing system changes — those are CEO triage decisions.
* Calling Anthropic / OpenRouter API.

Usage
-----
::

    python scripts/research/run_f12_us30_tolerance_sweep.py \\
        --output-dir research/ai_behavior/F12_us30_tolerance_sweep

    python scripts/research/run_f12_us30_tolerance_sweep.py \\
        --output-dir /tmp/scratch --dry-run

    python scripts/research/run_f12_us30_tolerance_sweep.py \\
        --output-dir /tmp/scratch --tolerance-ticks 5,10,20,50,100

The default sweep is ``5,10,20,50,100``; the spec list comes straight
from the F12 brief.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# Make project root importable when invoked as a file
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.hallucination_measurement import (  # noqa: E402
    DEFAULT_LIVE_EVALUATIONS_DIR,
    DEFAULT_OHLCV_DIR,
    DEFAULT_TRADE_RECORDS_DIR,
    EvaluationCheck,
    PriceClassification,
)

import scripts.research.run_f9_us30_hallucination_deepdive as f9  # noqa: E402

logger = logging.getLogger("f12_tolerance_sweep")

#: Harness identifier embedded in sweep.json.
HARNESS_VERSION_F12 = "F12-v1"

#: Default tolerance grid (per the F12 brief).
DEFAULT_TOLERANCE_GRID: Tuple[int, ...] = (5, 10, 20, 50, 100)

#: Anchor tolerance — the "baseline" against which flips are detected.
DEFAULT_BASELINE_TOLERANCE = 5

#: Number of US30 records F9 reports (49 evaluations × ~5 prices each).
TARGET_SYMBOL = f9.TARGET_SYMBOL  # "US30_cash"


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class ToleranceRow:
    """One row of the sweep table — the aggregate hallucination rate at
    a particular tolerance value.
    """

    tolerance_ticks: int
    n_evaluations: int = 0
    n_prices: int = 0
    n_accurate: int = 0
    n_hallucinated: int = 0
    n_misattributed: int = 0
    n_records_flipping_vs_baseline: int = 0  # populated by caller

    @property
    def hallucination_pct(self) -> Optional[float]:
        if self.n_prices == 0:
            return None
        return 100.0 * self.n_hallucinated / self.n_prices

    @property
    def accurate_pct(self) -> Optional[float]:
        if self.n_prices == 0:
            return None
        return 100.0 * self.n_accurate / self.n_prices

    @property
    def misattributed_pct(self) -> Optional[float]:
        if self.n_prices == 0:
            return None
        return 100.0 * self.n_misattributed / self.n_prices


# ---------------------------------------------------------------------------
# Stable per-classification identity
# ---------------------------------------------------------------------------


def classification_key(
    check: EvaluationCheck,
    cl: PriceClassification,
) -> Tuple[str, str, str, str, float]:
    """Produce a stable identity for a single AI-cited price across
    tolerance runs.

    A classification is identified by:
      * ``candle_time_utc`` — the candle that triggered the evaluation
      * ``record_source`` — ``trade_records`` or ``live_evaluations``
      * ``role`` — ``ob_mid``, ``stop_loss``, ``sweep_price``, ...
      * ``source_field`` — exact provenance string (handles the case
        where a single record cites the same role twice through
        different fields)
      * ``value`` — the AI-quoted price

    Across two F9 runs at different tolerances the same record produces
    classifications keyed on this tuple — which lets us compare status
    pairwise.
    """
    return (
        check.candle_time_utc or "",
        check.record_source or "",
        cl.role or "",
        cl.source_field or "",
        float(cl.value),
    )


def _checks_to_classification_map(
    checks: List[EvaluationCheck],
) -> Dict[Tuple[str, str, str, str, float], Tuple[EvaluationCheck, PriceClassification]]:
    """Flatten a list of checks into ``key → (check, classification)``."""
    out: Dict[Tuple[str, str, str, str, float], Tuple[EvaluationCheck, PriceClassification]] = {}
    for c in checks:
        for cl in c.classifications:
            if cl.classification is None:
                continue
            key = classification_key(c, cl)
            out[key] = (c, cl)
    return out


def _aggregate_to_row(
    tolerance: int,
    checks: List[EvaluationCheck],
) -> ToleranceRow:
    """Tally accurate/hallucinated/misattributed counts."""
    row = ToleranceRow(tolerance_ticks=tolerance, n_evaluations=len(checks))
    for c in checks:
        for cl in c.classifications:
            if cl.classification is None:
                continue
            row.n_prices += 1
            if cl.classification == "accurate":
                row.n_accurate += 1
            elif cl.classification == "hallucinated":
                row.n_hallucinated += 1
            elif cl.classification == "misattributed":
                row.n_misattributed += 1
    return row


# ---------------------------------------------------------------------------
# Core sweep
# ---------------------------------------------------------------------------


@dataclass
class FlippingRecord:
    """One classification whose status changes across tolerance values."""

    candle_time_utc: str
    record_source: str
    role: str
    source_field: str
    value: float
    period_month: Optional[str]
    period_half: Optional[str]
    framework: Optional[str]
    decision: Optional[str]
    #: status at each tolerance (in sweep order). E.g. {"5": "hallucinated", "10": "hallucinated", "50": "accurate"}.
    status_per_tolerance: Dict[str, str] = field(default_factory=dict)
    #: matched_mso_field at each tolerance (for traceability of *what* it matched at the wider window).
    matched_field_per_tolerance: Dict[str, Optional[str]] = field(default_factory=dict)
    #: matched_mso_value at each tolerance.
    matched_value_per_tolerance: Dict[str, Optional[float]] = field(default_factory=dict)
    #: delta_ticks at each tolerance.
    delta_ticks_per_tolerance: Dict[str, Optional[float]] = field(default_factory=dict)
    #: minimum tolerance at which this row first switched to ``accurate``,
    #: if any. ``None`` if it never switched.
    first_accurate_tolerance: Optional[int] = None


@dataclass
class SweepResult:
    """Top-level F12 sweep result."""

    harness_version_f12: str
    tolerances: List[int]
    baseline_tolerance: int
    rows: List[ToleranceRow]
    flipping_records: List[FlippingRecord]


def _build_flipping_records(
    *,
    per_tolerance_checks: Dict[int, List[EvaluationCheck]],
    tolerances: Sequence[int],
    baseline_tolerance: int,
) -> List[FlippingRecord]:
    """Walk every classification across the sweep grid and emit a row
    for those that change status compared to ``baseline_tolerance``.

    The same classification key may appear in every tolerance's
    classification map; if its status disagrees with the baseline at
    *any* point in the grid, we emit one ``FlippingRecord`` summarising
    the cross-tolerance picture.
    """
    if baseline_tolerance not in per_tolerance_checks:
        raise ValueError(
            f"baseline_tolerance={baseline_tolerance} not in tolerance grid {sorted(per_tolerance_checks)}"
        )

    # baseline map: every classification at the anchor tolerance
    baseline_map = _checks_to_classification_map(per_tolerance_checks[baseline_tolerance])

    flipping: Dict[Tuple[str, str, str, str, float], FlippingRecord] = {}

    # Build per-tolerance maps once
    tolerance_maps: Dict[int, Dict[Tuple[str, str, str, str, float], Tuple[EvaluationCheck, PriceClassification]]] = {
        t: _checks_to_classification_map(per_tolerance_checks[t]) for t in tolerances
    }

    # For every key that exists at baseline, compare across the grid
    for key, (base_check, base_cl) in baseline_map.items():
        baseline_status = base_cl.classification
        # Has any tolerance produced a different status?
        flipped = False
        statuses: Dict[str, str] = {}
        matched_fields: Dict[str, Optional[str]] = {}
        matched_values: Dict[str, Optional[float]] = {}
        delta_ticks: Dict[str, Optional[float]] = {}
        first_accurate: Optional[int] = None
        if baseline_status == "accurate":
            first_accurate = baseline_tolerance
        for t in tolerances:
            cur = tolerance_maps[t].get(key)
            if cur is None:
                # Should not happen: same input → same classification rows
                # (only the per-row CLASSIFICATION may change). Defensive
                # placeholder.
                statuses[str(t)] = "missing"
                matched_fields[str(t)] = None
                matched_values[str(t)] = None
                delta_ticks[str(t)] = None
                continue
            _, cur_cl = cur
            statuses[str(t)] = cur_cl.classification or "none"
            matched_fields[str(t)] = cur_cl.matched_mso_field
            matched_values[str(t)] = cur_cl.matched_mso_value
            delta_ticks[str(t)] = cur_cl.delta_ticks
            if cur_cl.classification != baseline_status:
                flipped = True
            if (
                cur_cl.classification == "accurate"
                and (first_accurate is None or t < first_accurate)
            ):
                first_accurate = t

        if not flipped:
            continue

        flipping[key] = FlippingRecord(
            candle_time_utc=key[0],
            record_source=key[1],
            role=key[2],
            source_field=key[3],
            value=key[4],
            period_month=base_check.period_month,
            period_half=base_check.period_half,
            framework=base_check.framework,
            decision=base_check.decision,
            status_per_tolerance=statuses,
            matched_field_per_tolerance=matched_fields,
            matched_value_per_tolerance=matched_values,
            delta_ticks_per_tolerance=delta_ticks,
            first_accurate_tolerance=first_accurate,
        )

    return sorted(
        flipping.values(),
        key=lambda r: (r.candle_time_utc, r.role, r.source_field),
    )


def run_sweep(
    *,
    trade_records_dir: Path,
    live_evaluations_dir: Path,
    ohlcv_dir: Path,
    tolerances: Sequence[int] = DEFAULT_TOLERANCE_GRID,
    baseline_tolerance: int = DEFAULT_BASELINE_TOLERANCE,
    project_root: Path = _PROJECT_ROOT,
) -> SweepResult:
    """Execute the F12 sweep end-to-end.

    For each tolerance value in ``tolerances`` (de-duplicated, sorted
    ascending) the function:

    1. Calls :func:`f9.run_deepdive` with that tolerance.
    2. Aggregates accurate / hallucinated / misattributed counts.
    3. Cross-references status against ``baseline_tolerance`` to
       detect per-classification flips.

    The resulting :class:`SweepResult` carries one row per tolerance +
    the flat list of every classification that changed status at any
    point in the grid.
    """
    sorted_tolerances = sorted({int(t) for t in tolerances})
    if baseline_tolerance not in sorted_tolerances:
        raise ValueError(
            f"baseline_tolerance={baseline_tolerance} must appear in "
            f"tolerance grid {sorted_tolerances}"
        )

    per_tolerance_checks: Dict[int, List[EvaluationCheck]] = {}
    rows: List[ToleranceRow] = []

    for t in sorted_tolerances:
        logger.info("Running F9 deepdive at tolerance_ticks=%d", t)
        _result, us30_checks = f9.run_deepdive(
            trade_records_dir=trade_records_dir,
            live_evaluations_dir=live_evaluations_dir,
            ohlcv_dir=ohlcv_dir,
            tolerance_ticks=t,
            project_root=project_root,
        )
        per_tolerance_checks[t] = us30_checks
        row = _aggregate_to_row(t, us30_checks)
        rows.append(row)

    # Flip detection
    flipping_records = _build_flipping_records(
        per_tolerance_checks=per_tolerance_checks,
        tolerances=sorted_tolerances,
        baseline_tolerance=baseline_tolerance,
    )

    # Now annotate rows with the flip count
    base_map = _checks_to_classification_map(per_tolerance_checks[baseline_tolerance])
    for row in rows:
        if row.tolerance_ticks == baseline_tolerance:
            row.n_records_flipping_vs_baseline = 0
            continue
        cur_map = _checks_to_classification_map(per_tolerance_checks[row.tolerance_ticks])
        flips = 0
        for k, (_c, base_cl) in base_map.items():
            cur = cur_map.get(k)
            if cur is None:
                continue
            if cur[1].classification != base_cl.classification:
                flips += 1
        row.n_records_flipping_vs_baseline = flips

    return SweepResult(
        harness_version_f12=HARNESS_VERSION_F12,
        tolerances=sorted_tolerances,
        baseline_tolerance=baseline_tolerance,
        rows=rows,
        flipping_records=flipping_records,
    )


# ---------------------------------------------------------------------------
# Verdict logic — H4 confirmation/refutation
# ---------------------------------------------------------------------------


def _h4_verdict(rows: List[ToleranceRow]) -> Tuple[str, str]:
    """Classify the sweep as Confirmed / Refuted / Partial.

    Rule (per F12 brief):
      * Confirmed — the rate at tol=50 drops below 10% (the brief
        nominates "23.4% → <10%" as a sharp confirmation signal).
      * Refuted — the rate stays elevated (≥20%) at tol=50; the offsets
        are real grounding failures, not precision rounding.
      * Partial — somewhere in between (drops, but not sharply).

    Returns (verdict_label, reasoning_paragraph).
    """
    by_t = {row.tolerance_ticks: row for row in rows}
    base = by_t.get(5)
    wide = by_t.get(50)
    if base is None or wide is None:
        return ("Indeterminate", "Sweep did not include both tolerance=5 and tolerance=50.")
    base_pct = base.hallucination_pct or 0.0
    wide_pct = wide.hallucination_pct or 0.0
    delta = base_pct - wide_pct

    if wide_pct < 10.0:
        verdict = "Confirmed"
        reason = (
            f"Hallucination rate dropped sharply from {base_pct:.1f}% at "
            f"tolerance=5 to {wide_pct:.1f}% at tolerance=50 (Δ={delta:.1f}pp). "
            f"This is consistent with H4 (45-50-tick midpoint precision rounding) — "
            f"records that were flagged hallucinated at tol=5 reclassify as "
            f"accurate once the tolerance window absorbs the systematic offset."
        )
    elif wide_pct >= 20.0 or delta < 5.0:
        verdict = "Refuted"
        reason = (
            f"Hallucination rate remained elevated at tolerance=50 "
            f"({base_pct:.1f}% → {wide_pct:.1f}%, Δ={delta:.1f}pp). H4 "
            f"(precision rounding) does not explain the bulk of the rate. "
            f"The offsets between AI-cited prices and MSO levels are real "
            f"grounding failures — the cited prices simply do not exist in "
            f"the MSO within ±50 ticks. This pushes the explanation onto "
            f"H1 (TP forward-derivation), H2 (entry outside OB), or H3 "
            f"(structured field cites different OB than explanation text)."
        )
    else:
        verdict = "Partial"
        reason = (
            f"Hallucination rate fell from {base_pct:.1f}% at tolerance=5 "
            f"to {wide_pct:.1f}% at tolerance=50 (Δ={delta:.1f}pp) — a "
            f"meaningful but non-dominant drop. H4 (precision rounding) "
            f"explains a subset of the cases but other root-cause "
            f"hypotheses (H1 forward-TP, H2 entry-outside-OB, H3 OB "
            f"role-disambiguation) remain in play."
        )
    return (verdict, reason)


# ---------------------------------------------------------------------------
# Output emission
# ---------------------------------------------------------------------------


def _row_to_dict(row: ToleranceRow) -> Dict[str, Any]:
    return {
        "tolerance_ticks": row.tolerance_ticks,
        "n_evaluations": row.n_evaluations,
        "n_prices": row.n_prices,
        "n_accurate": row.n_accurate,
        "n_hallucinated": row.n_hallucinated,
        "n_misattributed": row.n_misattributed,
        "accurate_pct": row.accurate_pct,
        "hallucination_pct": row.hallucination_pct,
        "misattributed_pct": row.misattributed_pct,
        "n_records_flipping_vs_baseline": row.n_records_flipping_vs_baseline,
    }


def _flipping_record_to_dict(rec: FlippingRecord) -> Dict[str, Any]:
    return {
        "candle_time_utc": rec.candle_time_utc,
        "record_source": rec.record_source,
        "role": rec.role,
        "source_field": rec.source_field,
        "value": rec.value,
        "period_month": rec.period_month,
        "period_half": rec.period_half,
        "framework": rec.framework,
        "decision": rec.decision,
        "status_per_tolerance": rec.status_per_tolerance,
        "matched_field_per_tolerance": rec.matched_field_per_tolerance,
        "matched_value_per_tolerance": rec.matched_value_per_tolerance,
        "delta_ticks_per_tolerance": rec.delta_ticks_per_tolerance,
        "first_accurate_tolerance": rec.first_accurate_tolerance,
    }


def write_sweep_json(result: SweepResult, path: Path) -> None:
    """Emit the machine-readable sweep result.

    Schema:
      {
        "harness_version_f12": str,
        "tolerances": [int, ...],
        "baseline_tolerance": int,
        "per_tolerance": [<row dict>, ...],
        "flipping_records": [<flip dict>, ...]
      }
    """
    payload: Dict[str, Any] = {
        "harness_version_f12": result.harness_version_f12,
        "tolerances": list(result.tolerances),
        "baseline_tolerance": result.baseline_tolerance,
        "per_tolerance": [_row_to_dict(r) for r in result.rows],
        "flipping_records": [_flipping_record_to_dict(r) for r in result.flipping_records],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_flipping_records_jsonl(records: List[FlippingRecord], path: Path) -> None:
    """One JSON object per line — every flipping classification.

    Schema per row:
      {candle_time_utc, record_source, role, source_field, value,
       period_month, period_half, framework, decision,
       status_per_tolerance: {"5": "...", "10": "...", ...},
       matched_field_per_tolerance, matched_value_per_tolerance,
       delta_ticks_per_tolerance, first_accurate_tolerance}
    """
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(_flipping_record_to_dict(rec)) + "\n")


def _fmt_pct(p: Optional[float]) -> str:
    if p is None:
        return "—"
    return f"{p:.1f}%"


def write_report_md(result: SweepResult, path: Path) -> None:
    """Emit the human-readable verdict block."""
    by_t = {row.tolerance_ticks: row for row in result.rows}
    verdict, reasoning = _h4_verdict(result.rows)

    lines: List[str] = []
    lines.append("# F12 — US30 Hallucination Tolerance Sweep")
    lines.append("")
    lines.append(
        f"Harness: F12=`{result.harness_version_f12}` consuming "
        f"F9=`{f9.HARNESS_VERSION_F9}` (B7 module under the hood)."
    )
    lines.append("")
    lines.append(
        "Tests F9's H4 hypothesis (45-50-tick midpoint precision rounding) by "
        "sweeping the price-match tolerance across "
        f"`{result.tolerances}` ticks and tracking which classifications flip "
        f"status vs the anchor `tolerance={result.baseline_tolerance}`."
    )
    lines.append("")

    lines.append("## US30 hallucination rate vs tolerance")
    lines.append("")
    lines.append(
        "| Tolerance (ticks) | Hallucination rate | n records flipping vs tol=5 |"
    )
    lines.append("|---:|---:|---:|")
    for t in result.tolerances:
        row = by_t[t]
        flips_label = "0 (baseline)" if t == result.baseline_tolerance else str(row.n_records_flipping_vs_baseline)
        lines.append(
            f"| {t} | {_fmt_pct(row.hallucination_pct)} | {flips_label} |"
        )
    lines.append("")

    base_row = by_t[result.baseline_tolerance]
    lines.append(
        f"_Baseline (tolerance={result.baseline_tolerance}): "
        f"{base_row.n_evaluations} US30 evaluations, "
        f"{base_row.n_prices} non-null classifications._"
    )
    lines.append("")

    # ------------------------------------------------------------------
    # Verdict
    # ------------------------------------------------------------------
    lines.append("## H4 verdict")
    lines.append(f"- **{verdict}**")
    lines.append(f"- Reasoning: {reasoning}")
    if verdict == "Confirmed":
        implication = (
            "US30 prompt research should treat the AI's `ob_mid` "
            "computation as a precision-rounding bug, not a grounding "
            "failure. A prompt-side fix could nudge the AI toward "
            "exact-tick-aligned midpoint quoting (or the L2 verifier "
            "could relax `h1_poi_exists` tolerance for US30 specifically)."
        )
    elif verdict == "Refuted":
        implication = (
            "The widened tolerance does not absorb the bulk of US30's "
            "hallucinations; the AI is citing prices that genuinely do "
            "not appear in the MSO it was given. US30 prompt research "
            "should focus on H1 (TP forward-derivation), H2 (entry "
            "outside OB), and H3 (structured-field/explanation "
            "contradiction) — not on precision rounding."
        )
    else:
        implication = (
            "US30 prompt research should pursue both branches in "
            "parallel: tighten precision-rounding handling for the "
            "subset that flipped, and address the grounding-failure "
            "subset that did not."
        )
    lines.append(f"- Implication for US30 prompt research: {implication}")
    lines.append("")

    # ------------------------------------------------------------------
    # Per-record flip pattern
    # ------------------------------------------------------------------
    lines.append("## Flipping classifications")
    lines.append("")
    lines.append(
        f"Total classifications that change status across the sweep: "
        f"**{len(result.flipping_records)}**."
    )
    lines.append("")

    if not result.flipping_records:
        lines.append(
            "_No classifications flip status — the same set of rows is "
            "marked hallucinated at every tolerance value tested._"
        )
        lines.append("")
    else:
        # Group by role so we can see whether the flipping is concentrated
        # on `ob_mid` (the H4-implicated role) or distributed across roles.
        by_role: Dict[str, List[FlippingRecord]] = {}
        for rec in result.flipping_records:
            by_role.setdefault(rec.role, []).append(rec)

        lines.append("### Flips by role")
        lines.append("")
        lines.append("| Role | n flipping | first_accurate_tolerance distribution |")
        lines.append("|---|---:|---|")
        for role in sorted(by_role.keys()):
            recs = by_role[role]
            tol_dist: Dict[str, int] = {}
            for r in recs:
                k = "never" if r.first_accurate_tolerance is None else str(r.first_accurate_tolerance)
                tol_dist[k] = tol_dist.get(k, 0) + 1
            tol_dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(tol_dist.items()))
            lines.append(f"| `{role}` | {len(recs)} | {tol_dist_str} |")
        lines.append("")

        # Top-10 flipping records (by smallest first_accurate_tolerance)
        top = sorted(
            result.flipping_records,
            key=lambda r: (
                r.first_accurate_tolerance if r.first_accurate_tolerance is not None else 1e9,
                r.role,
                r.candle_time_utc,
            ),
        )[:10]
        lines.append("### Top-10 records by first_accurate_tolerance")
        lines.append("")
        lines.append(
            "| candle_time_utc | role | value | first_acc_tol | "
            f"status@5 | status@50 | matched@first_acc |"
        )
        lines.append("|---|---|---:|---:|---|---|---|")
        for rec in top:
            f50 = rec.status_per_tolerance.get("50", "—")
            f5 = rec.status_per_tolerance.get("5", "—")
            fa = rec.first_accurate_tolerance
            mat_field = "—"
            if fa is not None:
                mat_field = rec.matched_field_per_tolerance.get(str(fa)) or "—"
            lines.append(
                f"| {rec.candle_time_utc} | `{rec.role}` | {rec.value} | "
                f"{fa if fa is not None else 'never'} | {f5} | {f50} | "
                f"`{mat_field}` |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "See `flipping_records.jsonl` for the full per-classification "
        "audit and `sweep.json` for the machine-readable result."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_tolerances(arg: str) -> List[int]:
    """Parse a comma-separated tolerance list into a sorted unique list of ints."""
    out: List[int] = []
    for piece in arg.split(","):
        piece = piece.strip()
        if not piece:
            continue
        try:
            v = int(piece)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"invalid tolerance value: {piece!r}"
            ) from exc
        if v <= 0:
            raise argparse.ArgumentTypeError(
                f"tolerance must be positive (got {v})"
            )
        out.append(v)
    if not out:
        raise argparse.ArgumentTypeError("empty tolerance list")
    return sorted(set(out))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_f12_us30_tolerance_sweep",
        description=(
            "F12 — US30 hallucination tolerance sweep. Tests F9's H4 "
            "(45-50-tick midpoint precision rounding) hypothesis by "
            "running F9's analysis at multiple tolerance values and "
            "auditing per-record flips. NO AI calls; pure-Python."
        ),
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for sweep.json + flipping_records.jsonl + report.md.",
    )
    p.add_argument(
        "--tolerance-ticks",
        type=_parse_tolerances,
        default=list(DEFAULT_TOLERANCE_GRID),
        help=(
            "Comma-separated tolerance grid in ticks (default "
            f"{','.join(str(t) for t in DEFAULT_TOLERANCE_GRID)})."
        ),
    )
    p.add_argument(
        "--baseline-tolerance",
        type=int,
        default=DEFAULT_BASELINE_TOLERANCE,
        help=(
            f"Anchor tolerance for flip detection (default {DEFAULT_BASELINE_TOLERANCE}). "
            "Must appear in the --tolerance-ticks grid."
        ),
    )
    p.add_argument(
        "--trade-records-dir",
        type=Path,
        default=DEFAULT_TRADE_RECORDS_DIR,
        help="Path to knowledge_base/trade_records/.",
    )
    p.add_argument(
        "--live-evaluations-dir",
        type=Path,
        default=DEFAULT_LIVE_EVALUATIONS_DIR,
        help="Path to knowledge_base/live_evaluations/.",
    )
    p.add_argument(
        "--ohlcv-dir",
        type=Path,
        default=DEFAULT_OHLCV_DIR,
        help="Path to data/historical_2026/ for the OHLCV lookback.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and exit 0 without writing.",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO-level logging.",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    print(f"# F12 US30 Tolerance Sweep — harness {HARNESS_VERSION_F12}")
    print(f"# Driving F9 module = {f9.HARNESS_VERSION_F9}")
    print(f"trade_records_dir   : {args.trade_records_dir}")
    print(f"live_evaluations_dir: {args.live_evaluations_dir}")
    print(f"ohlcv_dir           : {args.ohlcv_dir}")
    print(f"tolerance grid      : {args.tolerance_ticks}")
    print(f"baseline tolerance  : {args.baseline_tolerance}")
    print(f"output_dir          : {args.output_dir}")
    print(f"started             : {dt.datetime.now(dt.timezone.utc).isoformat()}")

    if args.dry_run:
        print("[DRY RUN] No writes. Exiting 0.")
        return 0

    if args.baseline_tolerance not in args.tolerance_ticks:
        print(
            f"[ERROR] baseline_tolerance={args.baseline_tolerance} not in "
            f"tolerance grid {args.tolerance_ticks}",
            file=sys.stderr,
        )
        return 2

    result = run_sweep(
        trade_records_dir=args.trade_records_dir,
        live_evaluations_dir=args.live_evaluations_dir,
        ohlcv_dir=args.ohlcv_dir,
        tolerances=args.tolerance_ticks,
        baseline_tolerance=args.baseline_tolerance,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    sweep_path = args.output_dir / "sweep.json"
    write_sweep_json(result, sweep_path)
    print(f"[wrote] {sweep_path}")

    flip_path = args.output_dir / "flipping_records.jsonl"
    write_flipping_records_jsonl(result.flipping_records, flip_path)
    print(f"[wrote] {flip_path}")

    report_path = args.output_dir / "report.md"
    write_report_md(result, report_path)
    print(f"[wrote] {report_path}")

    print(f"\nfinished : {dt.datetime.now(dt.timezone.utc).isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
