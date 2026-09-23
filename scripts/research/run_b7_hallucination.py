"""B7 — Hallucination Rate Systematic Measurement (CLI driver).

Drives :mod:`src.research_infra.hallucination_measurement` over every
historical evaluation we have on disk, computes the per-instrument /
per-period / per-framework / per-role hallucination rate, and emits

* ``rates.json`` — full machine-readable summary
* ``report.md``  — human-readable + verdict block

Phase 1 = $0 API. This script makes NO Anthropic / OpenRouter calls.

Usage
-----
Default full historical scan::

    python scripts/research/run_b7_hallucination.py \\
        --output-dir research/ai_behavior/B7_hallucination

Dry run (no writes)::

    python scripts/research/run_b7_hallucination.py \\
        --output-dir /tmp/scratch --dry-run

Custom tolerance::

    python scripts/research/run_b7_hallucination.py \\
        --output-dir research/ai_behavior/B7_hallucination \\
        --tolerance-ticks 10

Per memory ``project_research_scripts_missing_dotenv.md`` research scripts
do NOT auto-load ``.env``. This script does not read any environment
variable.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

# Make the project root importable when this script is invoked as a file.
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.hallucination_measurement import (  # noqa: E402
    DEFAULT_LIVE_EVALUATIONS_DIR,
    DEFAULT_OHLCV_DIR,
    DEFAULT_PERIOD_STRATEGY,
    DEFAULT_TOLERANCE_TICKS,
    DEFAULT_TRADE_RECORDS_DIR,
    HARNESS_VERSION,
    HARNESS_VERSION_V2,
    HallucinationRateRow,
    HallucinationReport,
    measure_from_disk,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_b7_hallucination",
        description=(
            "B7 — programmatic comparison of AI-stated price levels vs MSO raw_data "
            "across every historical evaluation. NO AI calls; pure-Python regex + "
            "structured-record join."
        ),
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for rates.json + report.md.",
    )
    p.add_argument(
        "--tolerance-ticks",
        type=int,
        default=DEFAULT_TOLERANCE_TICKS,
        help=f"Tolerance for price match in ticks (default {DEFAULT_TOLERANCE_TICKS}).",
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
        help="Path to data/historical_2026/ for the OHLCV lookback stand-in.",
    )
    p.add_argument(
        "--no-live-evaluations",
        action="store_true",
        help=(
            "Skip the live_evaluations corpus. Default is to include it as a "
            "coarse-arm signal alongside the precise trade_records arm."
        ),
    )
    # F13 — role-stratified emission. Default ON for new runs.
    p.add_argument(
        "--by-role-class",
        dest="by_role_class",
        action="store_true",
        default=True,
        help=(
            "F13 (B7-v2): also emit role-stratified rates_mso_grounded.json + "
            "report_by_role.md alongside the v1 rates.json + report.md. "
            "Default ON. The MSO_GROUNDED-only rate is the apples-to-apples "
            "grounding-failure metric (TP forward-derived artifact stripped)."
        ),
    )
    p.add_argument(
        "--no-by-role-class",
        dest="by_role_class",
        action="store_false",
        help="Disable F13 role-stratified emission (legacy v1-only output).",
    )
    p.add_argument(
        "--extra-live-evaluations-dir",
        type=Path,
        action="append",
        default=[],
        help=(
            "Additional live_evaluations-shaped JSONL corpora to fold in "
            "(repeatable). Used by F8 to add the H1-baseline reconstruction "
            "(``knowledge_base/live_evaluations_h1_reconstructed/``)."
        ),
    )
    p.add_argument(
        "--period-strategy",
        type=str,
        default=DEFAULT_PERIOD_STRATEGY,
        choices=["calendar_half", "intra_april_2026"],
        help=(
            "How to label H1/H2 periods. ``calendar_half`` (default) uses "
            "Jan-Jun→H1 / Jul-Dec→H2. ``intra_april_2026`` (F8) splits April "
            "2026 mid-month so the H1→H2 delta is computable on April-only data."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and exit 0 without writing.",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO-level logging from the underlying module.",
    )
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    # Plan
    print(f"# B7 Hallucination Measurement — harness {HARNESS_VERSION} "
          f"(+ {HARNESS_VERSION_V2} role-stratified: {args.by_role_class})")
    print(f"trade_records_dir   : {args.trade_records_dir}")
    print(f"live_evaluations_dir: {args.live_evaluations_dir}")
    if args.extra_live_evaluations_dir:
        print(f"extra_live_dirs     : {args.extra_live_evaluations_dir}")
    print(f"ohlcv_dir           : {args.ohlcv_dir}")
    print(f"include_live_evals  : {not args.no_live_evaluations}")
    print(f"period_strategy     : {args.period_strategy}")
    print(f"tolerance_ticks     : {args.tolerance_ticks}")
    print(f"by_role_class       : {args.by_role_class}")
    print(f"output_dir          : {args.output_dir}")
    print(f"started             : {dt.datetime.now(dt.timezone.utc).isoformat()}")

    if args.dry_run:
        print("[DRY RUN] No writes. Exiting 0.")
        return 0

    # Run
    report = measure_from_disk(
        trade_records_dir=args.trade_records_dir,
        live_evaluations_dir=args.live_evaluations_dir,
        ohlcv_dir=args.ohlcv_dir,
        tolerance_ticks=args.tolerance_ticks,
        include_live_evaluations=not args.no_live_evaluations,
        period_strategy=args.period_strategy,
        extra_live_evaluations_dirs=tuple(args.extra_live_evaluations_dir),
    )

    # Emit
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ---- v1 (all-roles) artifacts: rates.json + report.md ----
    summary_dict = report.to_summary_dict()

    rates_path = args.output_dir / "rates.json"
    report_path = args.output_dir / "report.md"

    # When --by-role-class is on, the v1 rates.json is renamed
    # rates_all.json to clarify it is the all-roles arm. We keep the
    # original rates.json for backward compatibility with downstream
    # consumers (and the original report.md path) when the flag is off.
    if args.by_role_class:
        rates_all_path = args.output_dir / "rates_all.json"
        with open(rates_all_path, "w", encoding="utf-8") as f:
            json.dump(summary_dict, f, indent=2)
        print(f"[wrote] {rates_all_path}")
        # Also write rates.json as a stable alias for backward compat.
        with open(rates_path, "w", encoding="utf-8") as f:
            json.dump(summary_dict, f, indent=2)
        print(f"[wrote] {rates_path} (alias)")
    else:
        with open(rates_path, "w", encoding="utf-8") as f:
            json.dump(summary_dict, f, indent=2)
        print(f"[wrote] {rates_path}")

    md = _build_report_md(report)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[wrote] {report_path}")

    # ---- F13 v2 (role-stratified) artifacts ----
    if args.by_role_class:
        rates_mso_path = args.output_dir / "rates_mso_grounded.json"
        with open(rates_mso_path, "w", encoding="utf-8") as f:
            json.dump({
                "harness_version": HARNESS_VERSION_V2,
                "tolerance_ticks": report.tolerance_ticks,
                "n_records_scanned": report.n_records_scanned,
                "n_records_with_classifications": report.n_records_with_classifications,
                "by_instrument_role_class": summary_dict["by_instrument_role_class"],
                "by_instrument_mso_grounded": summary_dict["by_instrument_mso_grounded"],
                "all_roles_per_instrument": summary_dict["by_instrument"],
                "comparison": _build_role_class_comparison(report),
            }, f, indent=2)
        print(f"[wrote] {rates_mso_path}")

        report_by_role_path = args.output_dir / "report_by_role.md"
        report_by_role_md = _build_report_by_role_md(report)
        with open(report_by_role_path, "w", encoding="utf-8") as f:
            f.write(report_by_role_md)
        print(f"[wrote] {report_by_role_path}")

    # Per-row JSONL artifact (useful for downstream forensic review)
    rows_path = args.output_dir / "rows.jsonl"
    with open(rows_path, "w", encoding="utf-8") as f:
        for r in report.rows:
            row = {
                "record_source": r.record_source,
                "symbol": r.symbol,
                "candle_time_utc": r.candle_time_utc,
                "period_month": r.period_month,
                "period_half": r.period_half,
                "decision": r.decision,
                "framework": r.framework,
                "realized_r": r.realized_r,
                "n_classifications": len(r.classifications),
                "n_accurate": sum(1 for c in r.classifications if c.classification == "accurate"),
                "n_hallucinated": sum(1 for c in r.classifications if c.classification == "hallucinated"),
                "n_misattributed": sum(1 for c in r.classifications if c.classification == "misattributed"),
                "classifications": [
                    {
                        "role": c.role,
                        "role_class": c.role_class,
                        "value": c.value,
                        "source_field": c.source_field,
                        "classification": c.classification,
                        "matched_mso_field": c.matched_mso_field,
                        "matched_mso_value": c.matched_mso_value,
                        "delta_ticks": c.delta_ticks,
                        "note": c.note,
                    }
                    for c in r.classifications
                ],
            }
            f.write(json.dumps(row) + "\n")
    print(f"[wrote] {rows_path}")

    print(f"\nfinished : {dt.datetime.now(dt.timezone.utc).isoformat()}")
    return 0


def _build_role_class_comparison(report: HallucinationReport):
    """Build a per-instrument old-vs-new comparison block."""
    out = []
    by_inst_all = {r.instrument: r for r in report.by_instrument}
    by_inst_mso = {r.instrument: r for r in report.by_instrument_mso_grounded}
    for inst, all_row in by_inst_all.items():
        mso_row = by_inst_mso.get(inst)
        delta_pp = None
        if all_row.hallucinated_pct is not None and mso_row is not None and mso_row.hallucinated_pct is not None:
            delta_pp = mso_row.hallucinated_pct - all_row.hallucinated_pct
        out.append({
            "instrument": inst,
            "all_roles_hallucinated_pct": all_row.hallucinated_pct,
            "all_roles_n_prices": all_row.n_prices,
            "mso_grounded_hallucinated_pct": mso_row.hallucinated_pct if mso_row else None,
            "mso_grounded_n_prices": mso_row.n_prices if mso_row else 0,
            "delta_pp": delta_pp,
        })
    return out


def _fmt_pct(p):
    if p is None:
        return "—"
    return f"{p:.1f}%"


def _build_report_md(report: HallucinationReport) -> str:
    """Render the human-readable report with the verdict block."""
    lines = []
    lines.append(f"# B7 — Hallucination Rate Systematic Measurement")
    lines.append("")
    lines.append(f"Harness: `{report.harness_version}` · "
                 f"tolerance_ticks: {report.tolerance_ticks} · "
                 f"records scanned: {report.n_records_scanned} · "
                 f"records with classifications: {report.n_records_with_classifications}")
    lines.append("")

    # ----- Per-instrument -----
    lines.append("## Hallucination rate matrix (per instrument)")
    lines.append("")
    lines.append("| Instrument | n_evals | n_prices | accurate% | hallucinated% | misattributed% |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in report.by_instrument:
        lines.append(f"| {r.instrument} | {r.n_evaluations} | {r.n_prices} | "
                     f"{_fmt_pct(r.accurate_pct)} | "
                     f"{_fmt_pct(r.hallucinated_pct)} | "
                     f"{_fmt_pct(r.misattributed_pct)} |")
    lines.append("")

    # ----- Per-instrument × period (H1/H2) -----
    lines.append("## Hallucination rate matrix (instrument × half-year)")
    lines.append("")
    lines.append("| Instrument | Period | n_evals | n_prices | accurate% | hallucinated% | misattributed% |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for r in report.by_instrument_period:
        lines.append(f"| {r.instrument} | {r.period} | {r.n_evaluations} | {r.n_prices} | "
                     f"{_fmt_pct(r.accurate_pct)} | "
                     f"{_fmt_pct(r.hallucinated_pct)} | "
                     f"{_fmt_pct(r.misattributed_pct)} |")
    lines.append("")

    # ----- Per-instrument × month (intra-period variance) -----
    lines.append("## Hallucination rate matrix (instrument × month)")
    lines.append("")
    lines.append("| Instrument | Month | n_evals | n_prices | accurate% | hallucinated% | misattributed% |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for r in report.by_instrument_month:
        lines.append(f"| {r.instrument} | {r.period} | {r.n_evaluations} | {r.n_prices} | "
                     f"{_fmt_pct(r.accurate_pct)} | "
                     f"{_fmt_pct(r.hallucinated_pct)} | "
                     f"{_fmt_pct(r.misattributed_pct)} |")
    lines.append("")

    # ----- Per-instrument × framework -----
    lines.append("## Hallucination rate matrix (instrument × framework)")
    lines.append("")
    lines.append("| Instrument | Framework | n_evals | n_prices | accurate% | hallucinated% | misattributed% |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for r in report.by_instrument_framework:
        lines.append(f"| {r.instrument} | {r.framework} | {r.n_evaluations} | {r.n_prices} | "
                     f"{_fmt_pct(r.accurate_pct)} | "
                     f"{_fmt_pct(r.hallucinated_pct)} | "
                     f"{_fmt_pct(r.misattributed_pct)} |")
    lines.append("")

    # ----- Per-role -----
    lines.append("## Hallucination rate by role (which price field decays the most)")
    lines.append("")
    lines.append("| Role | n_prices | accurate% | hallucinated% | misattributed% |")
    lines.append("|---|---:|---:|---:|---:|")
    role_rows_sorted = sorted(report.by_role,
                              key=lambda r: (r.n_prices == 0, -((r.n_hallucinated / r.n_prices) if r.n_prices else 0)))
    for r in role_rows_sorted:
        if r.n_prices == 0:
            continue
        lines.append(f"| {r.key} | {r.n_prices} | "
                     f"{_fmt_pct(r.accurate_pct)} | "
                     f"{_fmt_pct(r.hallucinated_pct)} | "
                     f"{_fmt_pct(r.misattributed_pct)} |")
    lines.append("")

    # ----- Strategic verdict -----
    lines.append("## Strategic verdict")
    lines.append("")
    if report.h1_h2_delta_pp is None:
        lines.append("H1→H2 hallucination delta: **NOT COMPUTABLE** — one or both halves "
                     "have no classifications. Coverage gap (live_evaluations spans only "
                     "April 2026; trade_records is April-only). Can be filled later by "
                     "running on H1-2026 simulator/replay outputs.")
    else:
        sign = "+" if report.h1_h2_delta_pp >= 0 else ""
        lines.append(f"H1→H2 hallucination delta: **{sign}{report.h1_h2_delta_pp:.2f}pp**")
    lines.append("")
    if report.most_hallucinated_role:
        most = next((r for r in report.by_role if r.key == report.most_hallucinated_role), None)
        if most:
            lines.append(f"Most-hallucinated price field: **{report.most_hallucinated_role}** "
                         f"({_fmt_pct(most.hallucinated_pct)} of {most.n_prices} prices)")
    else:
        lines.append("Most-hallucinated price field: **n/a** (no role had ≥5 classifications)")
    lines.append("")

    # Reasoning (auto-generated narrative based on data)
    lines.append("Reasoning:")
    if not report.by_instrument:
        lines.append("")
        lines.append("- No classifications were produced. Verify input directories are correct "
                     "and contain `trade_records/` JSON files (which alone carry MSO).")
    else:
        # Pick top hallucinator + comparator
        sorted_inst = sorted(report.by_instrument,
                             key=lambda r: -(r.hallucinated_pct or 0))
        top = sorted_inst[0]
        lines.append("")
        lines.append(f"- Top hallucination instrument: **{top.instrument}** at "
                     f"{_fmt_pct(top.hallucinated_pct)} (n_prices={top.n_prices}).")
        if len(sorted_inst) > 1:
            tail = sorted_inst[-1]
            lines.append(f"- Lowest hallucination instrument: **{tail.instrument}** at "
                         f"{_fmt_pct(tail.hallucinated_pct)} (n_prices={tail.n_prices}).")
        if report.h1_h2_delta_pp is not None:
            lines.append(f"- H1→H2 delta of {report.h1_h2_delta_pp:+.2f}pp is the most decay-relevant "
                         "datum here. A positive value says the AI's price-grounding got worse in "
                         "H2, consistent with system-decay; a near-zero value says hallucination is "
                         "NOT the decay mechanism (rule out, move to B12/B14/K53).")
        lines.append("- Coverage caveat: trade_records dataset is April-2026-only (CANDIDATEs); "
                     "live_evaluations dataset is also April-2026 only. The H1-2026 baseline is "
                     "missing on disk in this codebase. The number is informational at this stage; "
                     "K54 handoff should add a backfill task to extract the H1-2026 evaluation "
                     "stream (from logs/agent_*.log or batch_sessions if available).")
    lines.append("")

    # ----- Appendix: methodology -----
    lines.append("## Appendix — methodology summary")
    lines.append("")
    lines.append("- See `src/research_infra/docs/B7_hallucination.md` for the full methodology, "
                 "tolerance choice, classification rules, and K54 handoff.")
    lines.append("- Inputs: `knowledge_base/trade_records/{SYMBOL}/*.json` (precise: paired MSO+AI), "
                 "`knowledge_base/live_evaluations/{SYMBOL}/*.jsonl` (coarse: text + OHLCV), "
                 "`data/historical_2026/{SYMBOL}_H1.csv` (OHLCV stand-in).")
    lines.append("- Tolerance default: 5 ticks (per-instrument, see TICK_SIZE table in the module).")
    lines.append("- Classification: ACCURATE (same role match within tol), MISATTRIBUTED "
                 "(price exists in MSO but at different role), HALLUCINATED (no MSO match).")
    lines.append("- Out of scope: re-running AI on historical CANDs (Phase 2 A4); modifying "
                 "production code; proposing system changes (K54 handoff).")
    lines.append("")

    return "\n".join(lines)


def _build_report_by_role_md(report: HallucinationReport) -> str:
    """F13 — render the role-stratified report (B7-v2).

    Sections:

    1. The strategic verdict block (per-instrument all-roles vs
       MSO-grounded comparison).
    2. The per-instrument × per-role-class breakdown table.
    3. Methodology summary (taxonomy + rationale).
    """
    lines = []
    lines.append("# B7-v2 (F13) — Role-stratified hallucination rates")
    lines.append("")
    lines.append(
        f"Harness: `{HARNESS_VERSION_V2}` (additive on `{report.harness_version}`) · "
        f"tolerance_ticks: {report.tolerance_ticks} · "
        f"records scanned: {report.n_records_scanned} · "
        f"records with classifications: {report.n_records_with_classifications}"
    )
    lines.append("")
    lines.append(
        "**Why v2.** B7-v1 (`9611c58`) measured per-instrument hallucination "
        "rates but flagged TP at 38.5% hallucinated — a definitional artifact, "
        "since TP is forward-projected (entry + N×R), NOT drawn from the MSO. "
        "F9 (`cffb99c`) confirmed that 40.3% of US30's headline 23.4% rate "
        "came from this artifact. F13 stratifies cited prices into "
        "`MSO_GROUNDED` (real grounding-failure loci), `FORWARD_DERIVED` "
        "(forward-projected; hallucination measurement meaningless here), and "
        "`AMBIGUOUS` (case-by-case). The MSO-grounded rate is the apples-to-"
        "apples per-instrument comparison."
    )
    lines.append("")

    # ---- Strategic verdict (per-instrument old-vs-new) ----
    lines.append("## Per-instrument hallucination — old vs new methodology")
    lines.append("")
    lines.append("| Instrument | All-roles rate (original) | MSO-grounded rate (new) | n MSO-grounded | delta (pp) |")
    lines.append("|---|---:|---:|---:|---:|")

    by_inst_all = {r.instrument: r for r in report.by_instrument}
    by_inst_mso = {r.instrument: r for r in report.by_instrument_mso_grounded}
    # Sort by all-roles rate descending so the worst-on-paper instruments
    # are at the top and the re-ranking effect is most visible.
    sorted_insts = sorted(
        by_inst_all.keys(),
        key=lambda i: -(by_inst_all[i].hallucinated_pct or 0),
    )
    for inst in sorted_insts:
        all_row = by_inst_all[inst]
        mso_row = by_inst_mso.get(inst)
        all_pct = _fmt_pct(all_row.hallucinated_pct)
        mso_pct = _fmt_pct(mso_row.hallucinated_pct) if mso_row else "—"
        n_mso = str(mso_row.n_prices) if mso_row else "0"
        if (
            all_row.hallucinated_pct is not None
            and mso_row is not None
            and mso_row.hallucinated_pct is not None
        ):
            delta = mso_row.hallucinated_pct - all_row.hallucinated_pct
            delta_str = f"{delta:+.2f}"
        else:
            delta_str = "—"
        lines.append(f"| {inst} | {all_pct} | {mso_pct} | {n_mso} | {delta_str} |")
    lines.append("")

    # ---- Per-instrument × per-role-class detailed breakdown ----
    lines.append("## Per-instrument × per-role-class detailed breakdown")
    lines.append("")
    lines.append("| Instrument | Role class | n_evals | n_prices | accurate% | hallucinated% | misattributed% |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for r in report.by_instrument_role_class:
        lines.append(
            f"| {r.instrument} | {r.role_class} | {r.n_evaluations} | {r.n_prices} | "
            f"{_fmt_pct(r.accurate_pct)} | "
            f"{_fmt_pct(r.hallucinated_pct)} | "
            f"{_fmt_pct(r.misattributed_pct)} |"
        )
    lines.append("")

    # ---- Strategic verdict narrative ----
    lines.append("## Strategic verdict")
    lines.append("")
    if not by_inst_mso:
        lines.append("- No MSO-grounded rows produced. Verify input directories "
                     "are correct and contain `trade_records/` JSON files.")
    else:
        # Most-grounding-failure-prone instrument (MSO_GROUNDED only)
        worst_inst = max(
            by_inst_mso.values(),
            key=lambda r: (r.hallucinated_pct or 0, r.n_prices),
        )
        # US30 specific call-out (matches F9)
        us30 = by_inst_mso.get("US30_cash") or by_inst_mso.get("US30")
        us30_all = by_inst_all.get("US30_cash") or by_inst_all.get("US30")
        if us30 and us30_all and us30.hallucinated_pct is not None and us30_all.hallucinated_pct is not None:
            us30_artifact_pp = us30_all.hallucinated_pct - us30.hallucinated_pct
            lines.append(
                f"- US30's apparent hallucination rate before F13: "
                f"**{_fmt_pct(us30_all.hallucinated_pct)}**. "
                f"After stripping the FORWARD_DERIVED TP artifact: "
                f"**{_fmt_pct(us30.hallucinated_pct)}** "
                f"(artifact contribution: {us30_artifact_pp:+.2f}pp)."
            )
        lines.append(
            f"- Most-grounding-failure-prone instrument (MSO-grounded only): "
            f"**{worst_inst.instrument}** at "
            f"{_fmt_pct(worst_inst.hallucinated_pct)} "
            f"(n_prices={worst_inst.n_prices})."
        )
        # Detect ranking shifts: instruments whose rank changes between
        # all-roles and MSO-grounded.
        rank_all = {
            inst: i for i, inst in enumerate(sorted(
                by_inst_all.keys(),
                key=lambda i: -(by_inst_all[i].hallucinated_pct or 0),
            ))
        }
        rank_mso = {
            inst: i for i, inst in enumerate(sorted(
                by_inst_mso.keys(),
                key=lambda i: -(by_inst_mso[i].hallucinated_pct or 0),
            ))
        }
        shifts = [
            inst for inst in rank_all
            if inst in rank_mso and rank_all[inst] != rank_mso[inst]
        ]
        if shifts:
            lines.append(
                f"- Per-instrument ranking SHIFTS after role-stratification: "
                f"{sorted(shifts)} change rank between all-roles and "
                f"MSO-grounded views. Per-instrument comparison was NOT "
                f"apples-to-apples under v1."
            )
        else:
            lines.append(
                "- Per-instrument ranking is STABLE across all-roles and "
                "MSO-grounded views — but the absolute rates change."
            )

    lines.append("")
    # ---- Reasoning (auto-generated) ----
    lines.append("## Reasoning")
    lines.append("")
    lines.append(
        "- The MSO-grounded rate is the apples-to-apples grounding-failure "
        "metric. Under v1, instruments whose AI emits more TPs (because "
        "more CANDIDATEs fire) appeared more hallucination-prone purely as "
        "a measurement artifact. Stripping FORWARD_DERIVED roles isolates "
        "the real grounding-failure rate."
    )
    lines.append(
        "- For Phase 2 prompt research (K54+) the MSO-grounded rate is the "
        "decision-relevant number. A tool-use grounding step or a tightened "
        "L2 verifier targets MSO_GROUNDED roles only — improving "
        "FORWARD_DERIVED \"hallucination\" is not a coherent goal."
    )
    lines.append(
        "- The FORWARD_DERIVED column is informational: it reports what "
        "fraction of TPs map onto an MSO band by accident. A high value "
        "would suggest the AI's TP placement is structurally anchored to "
        "MSO levels (a structural feature, not a hallucination); a low "
        "value confirms TP is genuinely forward-projected."
    )
    lines.append("")

    # ---- Methodology / taxonomy ----
    lines.append("## Methodology — role taxonomy")
    lines.append("")
    lines.append(
        "Every cited price gets a `role_class` according to "
        "`src.research_infra.hallucination_measurement.ROLE_TAXONOMY`:"
    )
    lines.append("")
    lines.append("- **MSO_GROUNDED** — should match MSO data (real hallucination loci).")
    lines.append("  - `current_price`, `entry_price`, `stop_loss`")
    lines.append("  - `ob_high`, `ob_low`, `ob_mid`, `ob_body`")
    lines.append("  - `breaker_high`, `breaker_low`, `breaker_mid`")
    lines.append("  - `fvg_high`, `fvg_low`, `fvg_mid`")
    lines.append("  - `swing_high`, `swing_low`, `protected_swing`")
    lines.append("  - `sweep_price`, `liquidity_high`, `liquidity_low`")
    lines.append("- **FORWARD_DERIVED** — not in MSO by construction.")
    lines.append("  - `take_profit` (entry + N×R)")
    lines.append("  - `trailing_stop_target`")
    lines.append("- **AMBIGUOUS** — case-by-case.")
    lines.append("  - `equilibrium`")
    lines.append("")
    lines.append(
        "Unknown / novel roles default to AMBIGUOUS so they do not silently "
        "inflate the MSO-grounded rate. New canonical roles must be added "
        "to `ROLE_TAXONOMY` explicitly."
    )
    lines.append("")
    lines.append(
        "Recommended rate for downstream consumers (K54 + Phase 2 prompt "
        "research): **MSO_GROUNDED hallucinated_pct only**. The all-roles "
        "rate from v1 conflates real grounding failures with the TP "
        "forward-derivation artifact."
    )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
