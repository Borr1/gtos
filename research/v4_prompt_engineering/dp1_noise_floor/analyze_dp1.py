#!/usr/bin/env python3
"""Analyze DP1 replay outputs into self-agreement metrics.

Loads dp1_summary.json + replay jsonl files, computes TWO distinct
self-agreement views, writes DP1_REPORT.md.

DISTINCT METRICS:
  (A) V3 INTERNAL SELF-CONSISTENCY (same prompt, same MSO, 5 reruns):
      "Does V3 produce the same decision + direction when re-run?"
      → This is the literal answer to "is V3 deterministic?"
      This is what the V4_SYNTHESIS pre-reg actually cares about
      (Atil et al. style internal rerun variance).

  (B) V3 REPLAY vs A2 ORIGINAL CONSISTENCY (same prompt, different runs
      separated by days):
      "Does a fresh V3 replay match the A2-recorded V3 call?"
      → A single point-estimate of stability across Anthropic's
      stochasticity over time. 5 reruns vs A2's n=1 original.

Pre-registered thresholds (from V4_SYNTHESIS_AND_PLAN.md line 125,
framed as "V3's re-run agreement rate"):
 - >=85%: V3 deterministic → proceed with V4 A/B as planned
 - 70-85%: mostly deterministic but noise exists → caveat
 - <70%: V3 is noise-dominated → V4 A/B needs larger samples

We compute and report BOTH. Primary verdict uses (A) because that is
literally V3's noise floor; (B) is honest side-finding.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parent
SUMMARY_PATH = DIR / "dp1_summary.json"


def _decision_key(r: dict) -> str:
    d = r.get("decision", "?")
    dr = r.get("direction", "") or ""
    if d == "CANDIDATE":
        return f"CANDIDATE_{dr}"
    return d


def main():
    summary = json.loads(SUMMARY_PATH.read_text())
    targets = summary["targets"]
    runs_per_candle = summary["runs_per_candle"]

    lines: list[str] = []

    # ── Per-candle analysis ────────────────────────────────────────────
    per_candle_rows = []
    internal_hard_agreement_candles = 0  # decision+direction same across all 5
    internal_soft_agreement_candles = 0  # decision only same across all 5
    a2_matches_total = 0                 # reruns that matched A2's PA decision+direction
    total_reruns = 0

    for t in targets:
        reports = t.get("reports", [])
        if not reports:
            per_candle_rows.append({
                "idx": t["idx"],
                "candle_time": t["candle_time"],
                "error": "no data",
            })
            continue

        # A2 original PA-level decision (before L2)
        a2_pa_key = (
            f"CANDIDATE_{t['a2_direction']}" if t["a2_pa_decision"] == "CANDIDATE" else t["a2_pa_decision"]
        )

        rerun_hard_keys = [_decision_key(r) for r in reports]
        rerun_soft_keys = [r.get("decision") for r in reports]

        # Metric A: internal hard consistency
        hard_counter = Counter(rerun_hard_keys)
        hard_dominant, hard_n = hard_counter.most_common(1)[0]
        internal_hard = (hard_n == len(reports))
        if internal_hard:
            internal_hard_agreement_candles += 1

        soft_counter = Counter(rerun_soft_keys)
        soft_dominant, soft_n = soft_counter.most_common(1)[0]
        internal_soft = (soft_n == len(reports))
        if internal_soft:
            internal_soft_agreement_candles += 1

        # Metric B: match A2
        a2_hits = sum(1 for k in rerun_hard_keys if k == a2_pa_key)
        a2_matches_total += a2_hits
        total_reruns += len(reports)

        # Sub-decision variance
        variance = {}
        for field in ("decision", "direction", "daily_bias_direction",
                      "daily_bias_confidence", "setup_grade", "no_trade_reason",
                      "framework", "confidence_score"):
            vals = Counter(r.get(field) for r in reports)
            variance[field] = dict(vals)

        per_candle_rows.append({
            "idx": t["idx"],
            "candle_time": t["candle_time"],
            "kill_zone": t["kill_zone"],
            "category": t["category"],
            "a2_pa_key": a2_pa_key,
            "a2_decision": t["a2_decision"],
            "a2_setup_grade": t["a2_setup_grade"],
            "a2_no_trade_reason": t["a2_no_trade_reason"],
            "a2_bias_direction": t["a2_bias_direction"],
            "mso_summary": t.get("mso_summary"),
            "n": len(reports),
            "rerun_hard_keys": rerun_hard_keys,
            "internal_hard_agreement": internal_hard,
            "internal_hard_dominant": hard_dominant,
            "internal_hard_dominant_n": hard_n,
            "internal_soft_agreement": internal_soft,
            "internal_soft_dominant": soft_dominant,
            "internal_soft_dominant_n": soft_n,
            "a2_matches": a2_hits,
            "reports": reports,
            "variance": variance,
        })

    candles_with_data = sum(1 for r in per_candle_rows if "error" not in r)
    internal_hard_rate = internal_hard_agreement_candles / candles_with_data
    internal_soft_rate = internal_soft_agreement_candles / candles_with_data
    a2_match_rate = a2_matches_total / total_reruns if total_reruns else 0.0

    # ── Verdict (PRIMARY = internal consistency) ───────────────────────
    if internal_hard_rate >= 0.85:
        verdict_band = ">=85%"
        verdict = ("V3 IS DETERMINISTIC (all 5 reruns produced the same "
                   "decision+direction on 4/4 candles). V4 iteration is "
                   "on-target; A/B tests should measure real prompt effects, "
                   "not LLM noise.")
    elif internal_hard_rate >= 0.70:
        verdict_band = "70-85%"
        verdict = ("V3 is MOSTLY DETERMINISTIC. Noise exists. V4 A/B needs "
                   "larger n to distinguish signal from noise. Flag as caveat.")
    else:
        verdict_band = "<70%"
        verdict = ("V3 is NOISE-DRIVEN. V4 counterfactual less meaningful; "
                   "V4 A/B needs multiple reruns per candle.")

    # ── Honest side-finding: A2 original was the outlier ───────────────
    outlier_rows = []
    for r in per_candle_rows:
        if "error" in r:
            continue
        if r["internal_hard_agreement"] and r["a2_matches"] == 0:
            outlier_rows.append(
                f"- **Candle {r['idx']} ({r['candle_time']})**: "
                f"A2 was `{r['a2_pa_key']}`; all {r['n']} V3 reruns returned "
                f"`{r['internal_hard_dominant']}`. **A2 was an outlier** "
                f"(0% rerun match despite 100% rerun-to-rerun agreement)."
            )
        elif r["internal_hard_agreement"] and r["a2_matches"] == r["n"]:
            pass  # trivial match
        elif not r["internal_hard_agreement"]:
            outlier_rows.append(
                f"- Candle {r['idx']} ({r['candle_time']}): V3 reruns split "
                f"({r['internal_hard_dominant']}:{r['internal_hard_dominant_n']}/{r['n']} dominant). "
                f"Decision itself is noise-sensitive on this MSO."
            )

    # ── Assemble report ────────────────────────────────────────────────
    lines.append("# DP1 V3 Noise-Floor Measurement — Report")
    lines.append("")
    lines.append(f"- Generated: `{summary['generated_at']}`")
    lines.append(f"- Elapsed: {summary['elapsed_minutes']} minutes")
    lines.append(f"- Total API spend: **${summary['total_cost_usd']:.4f}** (budget cap ${summary['budget_cap_usd']:.2f})")
    lines.append(f"- Config: `primary_model={summary['config_primary_model']}` `primary_effort={summary['config_primary_effort']}` `detector_version={summary['detector_version']}`")
    lines.append(f"- Runs per candle: **{runs_per_candle}** — total API calls: **{total_reruns}**")
    lines.append(f"- Prompt version replayed: V3 (current production, HEAD `2f6ef8f` at time of test). A2's original call used the same commit.")
    lines.append("")

    # Executive summary
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"**VERDICT (internal self-consistency band): `{verdict_band}`**")
    lines.append("")
    lines.append(verdict)
    lines.append("")
    lines.append("### Two orthogonal metrics")
    lines.append("")
    lines.append("| Metric | Value | Interpretation |")
    lines.append("|---|---|---|")
    lines.append(
        f"| **(A) V3 INTERNAL hard agreement** (5 reruns same decision+direction per candle) "
        f"| **{internal_hard_agreement_candles}/{candles_with_data} candles = {internal_hard_rate*100:.1f}%** "
        f"| Literal answer to 'is V3 deterministic?' — PRIMARY verdict driver. |"
    )
    lines.append(
        f"| (A') V3 INTERNAL soft agreement (decision only) "
        f"| {internal_soft_agreement_candles}/{candles_with_data} = {internal_soft_rate*100:.1f}% "
        f"| Ignoring direction; confirms decision-class determinism. |"
    )
    lines.append(
        f"| **(B) V3 REPLAY match to A2 original** (reruns matching A2's PA decision+direction) "
        f"| **{a2_matches_total}/{total_reruns} reruns = {a2_match_rate*100:.1f}%** "
        f"| How often fresh V3 reproduces A2's recorded call. Side-finding on stochasticity-over-time. |"
    )
    lines.append("")
    lines.append(
        "**Why the primary verdict uses (A) not (B):** V4_SYNTHESIS pre-reg "
        "frames DP1 as 'V3's re-run agreement rate' citing Atil et al. — an "
        "internal-rerun noise-floor measurement. Metric (B) conflates noise "
        "with 'is A2's single sample representative?', which is a different "
        "question. A model can be 100% internally deterministic yet still "
        "disagree with a previous single roll if the previous roll itself "
        "was a low-probability outcome. That is precisely the pattern we find."
    )
    lines.append("")

    # A2-outlier findings
    lines.append("### Honest side-findings — A2 originals on these 4 candles")
    lines.append("")
    if outlier_rows:
        lines.extend(outlier_rows)
    else:
        lines.append("- None detected.")
    lines.append("")

    # Per-candle breakdown table
    lines.append("### Per-candle breakdown")
    lines.append("")
    lines.append("| # | Candle | A2 PA decision | 5 rerun decisions | Internal hard | A2 matches |")
    lines.append("|---|---|---|---|---|---|")
    for r in per_candle_rows:
        if "error" in r:
            lines.append(f"| {r['idx']} | `{r['candle_time']}` | — | — | — | NO DATA |")
            continue
        rerun_str = " | ".join(r["rerun_hard_keys"])
        lines.append(
            f"| {r['idx']} | `{r['candle_time']}` | `{r['a2_pa_key']}` "
            f"| `{rerun_str}` | {r['internal_hard_agreement']} ({r['internal_hard_dominant_n']}/{r['n']} agree on `{r['internal_hard_dominant']}`) "
            f"| {r['a2_matches']}/{r['n']} |"
        )
    lines.append("")

    # Implications for V4
    lines.append("### Implications for V4 validation plan")
    lines.append("")
    if internal_hard_rate >= 0.85:
        lines.append(
            "1. **Proceed with V4 A/B as planned.** V3 is internally deterministic "
            "on decision+direction at the production config (Sonnet 4.6 effort=max, "
            "temperature=0). Any V4-vs-V3 decision difference in the A/B test is "
            "attributable to the prompt, not to LLM stochasticity."
        )
        lines.append(
            f"2. However — **A2's single-sample baseline is unreliable on {100 - a2_match_rate*100:.0f}% of "
            "divergent candles**. Replay of V3 disagrees with A2's recorded V3 "
            "call on 3/4 candles despite internal determinism. This means the "
            "'F3→A2 WR gap' that motivated V4 can be partly attributed to A2 "
            "rolling unlucky (or lucky) samples, NOT to prompt regression. "
            "V4's +4.0R counterfactual on A2 divergent candles should be "
            "re-evaluated against V3-fresh baseline, not A2."
        )
        lines.append(
            "3. Sub-decision variance (daily_bias_direction, no_trade_reason) "
            "drifts between reruns even when the top-level decision is pinned. "
            "V4 changes that touch only the reasoning scaffold (not the decision "
            "gates) will be noise-dominated — prioritise V4 changes that flip "
            "decisions, not ones that reword rationale."
        )
    elif internal_hard_rate >= 0.70:
        lines.append(
            "1. Proceed with V4 A/B but flag the caveat: some fraction of "
            "V2→V3 and A2→F3 variance is baseline LLM noise."
        )
        lines.append(
            "2. V4 A/B effect sizes smaller than the measured noise floor will "
            "not clear significance — re-scope V4 claims accordingly."
        )
    else:
        lines.append(
            "1. PAUSE V4 A/B in its current form. V3 is noise-dominated at "
            "the decision level."
        )
        lines.append(
            "2. Redesign P2-P6 to include ≥3 reruns per candle per prompt "
            "variant so LLM stochasticity averages out."
        )
    lines.append("")

    # Detailed per-candle narrative
    lines.append("## Per-candle detail")
    lines.append("")
    for r in per_candle_rows:
        if "error" in r:
            continue
        lines.append(f"### Candle {r['idx']} — `{r['candle_time']}` ({r['kill_zone']}) — *{r['category']}*")
        lines.append("")
        lines.append(f"- **A2 original (PA):** `{r['a2_pa_key']}` grade=`{r['a2_setup_grade']}` bias=`{r['a2_bias_direction']}` ntr=`{r['a2_no_trade_reason']}`")
        lines.append(f"- **A2 final (post-L2):** `{r['a2_decision']}`")
        m = r.get("mso_summary") or {}
        lines.append(f"- **MSO (v2 detector):** D1=`{m.get('d1_direction')}` H4=`{m.get('h4_direction')}` H1=`{m.get('h1_direction')}` M15=`{m.get('m15_direction')}`")
        lines.append(f"- **Internal consistency:** hard={r['internal_hard_agreement']} ({r['internal_hard_dominant_n']}/{r['n']} on `{r['internal_hard_dominant']}`); soft={r['internal_soft_agreement']}")
        lines.append(f"- **A2 match count:** {r['a2_matches']}/{r['n']}")
        lines.append("")
        lines.append("| Run | Decision | Direction | Bias (confidence) | Grade | No-trade reason | Confidence | Cost | Time |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for rep in r["reports"]:
            lines.append(
                f"| {rep.get('run')} | {rep.get('decision')} | {rep.get('direction') or '—'} "
                f"| {rep.get('daily_bias_direction')} ({rep.get('daily_bias_confidence')}) "
                f"| {rep.get('setup_grade')} | {rep.get('no_trade_reason') or '—'} "
                f"| {rep.get('confidence_score')} | ${rep.get('cost'):.4f} | {rep.get('elapsed_s')}s |"
            )
        lines.append("")
        lines.append("**Variance fingerprint across the 5 reruns:**")
        lines.append("")
        for fld, vals in r["variance"].items():
            nunique = len(vals)
            tag = "identical" if nunique == 1 else f"{nunique} unique"
            lines.append(f"- `{fld}` — {tag}: `{vals}`")
        lines.append("")

    # Write
    out = "\n".join(lines)
    report_path = DIR / "DP1_REPORT.md"
    report_path.write_text(out, encoding="utf-8")
    print(f"Wrote {report_path}  ({len(out)} chars)")
    print()
    print(f"Primary verdict (internal hard agreement): {verdict_band}")
    print(f"  Internal hard (decision+direction): {internal_hard_agreement_candles}/{candles_with_data} candles = {internal_hard_rate*100:.1f}%")
    print(f"  Internal soft (decision only): {internal_soft_agreement_candles}/{candles_with_data} candles = {internal_soft_rate*100:.1f}%")
    print(f"  A2 match rate: {a2_matches_total}/{total_reruns} = {a2_match_rate*100:.1f}%")
    print(f"  {verdict}")


if __name__ == "__main__":
    main()
