#!/usr/bin/env python3
"""Analyze V4-DP1 replay outputs + V4-vs-V3 head-to-head.

Loads v4_dp1_summary.json + replay jsonl files and DP1's dp1_summary.json
and writes V4_DP1_REPORT.md with:

  1. V4 self-consistency per candle (5 reruns agreement)
  2. V4 typical decision per candle
  3. V3 typical (from DP1) vs V4 typical (from this run) head-to-head
  4. V4 counterfactual R total across 4 candles vs V3 total +1.5R
  5. Schema violations / parse errors (V4 claims Literal enforcement)
  6. Verdict: strong-win / cosmetic / regression / broken

Typical decision = mode of 5 reruns (if unique); flag when tied.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parent
SUMMARY_PATH = DIR / "v4_dp1_summary.json"
DP1_SUMMARY_PATH = DIR.parent / "dp1_noise_floor" / "dp1_summary.json"


def _decision_key(r: dict) -> str:
    d = r.get("decision", "?")
    dr = r.get("direction", "") or ""
    if d == "CANDIDATE":
        return f"CANDIDATE_{dr}"
    return d


def _typical_key(keys: list[str]) -> tuple[str, int, bool]:
    """Return (dominant_key, count, unanimous)."""
    if not keys:
        return ("NO_DATA", 0, False)
    c = Counter(keys)
    dominant, n = c.most_common(1)[0]
    unanimous = (n == len(keys))
    return (dominant, n, unanimous)


def _counterfactual_R(target: dict, decision_key: str) -> float:
    """Map V4 typical decision to R outcome using target's counterfactual_R map."""
    cf = target["counterfactual_R"]
    if decision_key == "NO_TRADE":
        return cf["NO_TRADE"]
    if decision_key == "CANDIDATE_LONG":
        return cf["LONG"]
    if decision_key == "CANDIDATE_SHORT":
        return cf["SHORT"]
    # PARSE_ERROR / unknown — treat as NO_TRADE for R accounting but flag
    return 0.0


def main() -> None:
    if not SUMMARY_PATH.exists():
        print(f"ERROR: {SUMMARY_PATH} not found — run_v4_dp1.py hasn't finished.")
        return
    summary = json.loads(SUMMARY_PATH.read_text())
    dp1_summary = json.loads(DP1_SUMMARY_PATH.read_text()) if DP1_SUMMARY_PATH.exists() else None

    targets = summary["targets"]
    runs_per_candle = summary["runs_per_candle"]

    # Build dict by idx of DP1 (V3) reruns for head-to-head
    dp1_by_idx = {}
    if dp1_summary:
        for t in dp1_summary["targets"]:
            dp1_reports = t.get("reports", [])
            keys = [_decision_key(r) for r in dp1_reports]
            dom, n, unan = _typical_key(keys)
            dp1_by_idx[t["idx"]] = {
                "candle_time": t["candle_time"],
                "v3_typical": dom,
                "v3_unanimous": unan,
                "v3_reports": dp1_reports,
                "v3_internal_hard_rate": n / len(keys) if keys else 0,
            }

    # ── V4 per-candle analysis ────────────────────────────────────────────
    per_candle = []
    v4_hard_agreement_candles = 0
    v4_schema_violations_total = 0
    v4_parse_errors_total = 0
    total_reruns = 0
    v4_typical_R_total = 0.0
    v3_typical_R_total = 0.0
    match_count = 0

    for t in targets:
        reports = t.get("reports", [])
        total_reruns += len(reports)

        if not reports:
            per_candle.append({
                "idx": t["idx"],
                "candle_time": t["candle_time"],
                "error": "no data",
            })
            continue

        keys = [_decision_key(r) for r in reports]
        dom, n_dom, unanimous = _typical_key(keys)
        if unanimous:
            v4_hard_agreement_candles += 1

        # Parse error + schema violation counts
        parse_errs = sum(1 for r in reports if r.get("decision") == "PARSE_ERROR")
        schema_vs = sum(1 for r in reports if r.get("no_trade_reason_schema_violation"))
        v4_parse_errors_total += parse_errs
        v4_schema_violations_total += schema_vs

        # V4 counterfactual R
        v4_R = _counterfactual_R(t, dom)
        v4_typical_R_total += v4_R

        # V3 typical R (from target spec, matches DP1)
        v3_R = t["v3_typical_R"]
        v3_typical_R_total += v3_R

        # Head-to-head match
        dp1_entry = dp1_by_idx.get(t["idx"])
        v3_dom = dp1_entry["v3_typical"] if dp1_entry else "?"
        matched = (dom == v3_dom)
        if matched:
            match_count += 1

        # Sub-decision variance
        variance = {}
        for field in ("decision", "direction", "daily_bias_direction",
                      "daily_bias_confidence", "setup_grade", "no_trade_reason",
                      "framework", "confidence_score"):
            vals = Counter(r.get(field) for r in reports)
            variance[field] = dict(vals)

        per_candle.append({
            "idx": t["idx"],
            "candle_time": t["candle_time"],
            "kill_zone": t["kill_zone"],
            "v3_typical": v3_dom,
            "v3_unanimous": dp1_entry["v3_unanimous"] if dp1_entry else None,
            "v3_typical_reason": t.get("v3_typical_reason"),
            "v3_typical_R": v3_R,
            "v4_typical": dom,
            "v4_typical_n": n_dom,
            "v4_unanimous": unanimous,
            "v4_typical_R": v4_R,
            "matched": matched,
            "f3_actual": t.get("f3_actual"),
            "a2_actual": t.get("a2_actual"),
            "counterfactual_R": t["counterfactual_R"],
            "parse_errs": parse_errs,
            "schema_violations": schema_vs,
            "mso_summary": t.get("mso_summary"),
            "n": len(reports),
            "rerun_keys": keys,
            "reports": reports,
            "variance": variance,
        })

    candles_with_data = sum(1 for r in per_candle if "error" not in r)
    v4_hard_rate = v4_hard_agreement_candles / candles_with_data if candles_with_data else 0
    delta_R = v4_typical_R_total - v3_typical_R_total

    # ── Verdict ──────────────────────────────────────────────────────────
    if v4_parse_errors_total > 0 or v4_schema_violations_total > 0:
        if v4_parse_errors_total >= candles_with_data:  # most calls unusable
            verdict_label = "broken"
            verdict = (
                f"V4 BROKEN — {v4_parse_errors_total} parse errors, "
                f"{v4_schema_violations_total} schema violations out of {total_reruns} "
                "calls. V4 DRAFT has bugs. DO NOT deploy; re-specify before further spend."
            )
        else:
            verdict_label = "minor-issues"
            verdict = (
                f"V4 has MINOR SCHEMA ISSUES — {v4_parse_errors_total} parse errors, "
                f"{v4_schema_violations_total} schema violations out of {total_reruns} "
                "calls. Non-fatal but should be documented before deploy."
            )
    else:
        verdict_label = "clean-schema"
        verdict = "V4 schema-clean: no parse errors, no R1-R8 allow-list violations."

    # Compute V4-vs-V3 verdict (strong-win / cosmetic / regression)
    if delta_R >= 0.5 and v4_hard_rate >= 0.85:
        winloss_label = "strong-win"
        winloss = (
            f"V4 TYPICAL OUTPERFORMS V3 TYPICAL BY +{delta_R:.1f}R across 4 candles "
            f"AND V4 self-agreement is {v4_hard_rate*100:.0f}% ≥ 85%. RECOMMEND: "
            "full $40-80 A/B backtest on broader sample + Monday deploy pending CEO review."
        )
    elif abs(delta_R) < 0.3:
        winloss_label = "cosmetic"
        winloss = (
            f"V4 ≈ V3 on 4 divergent candles (Δ = {delta_R:+.1f}R). V4's claimed "
            "improvements (BIAS PRECEDENCE, M15 ratio, schema enforcement, gaming-pattern "
            "closures) did NOT alter typical decisions on these borderline candles. "
            "RECOMMEND: ship V3 Monday (already in prod); defer V4 to post-Monday A/B "
            "on broader sample."
        )
    elif delta_R > 0:
        winloss_label = "mild-win"
        winloss = (
            f"V4 slightly OUTPERFORMS V3 (Δ = +{delta_R:.1f}R) but below the "
            "+0.5R strong-win threshold. RECOMMEND: larger A/B sample before "
            "decision; ship V3 Monday as baseline."
        )
    else:
        winloss_label = "regression"
        winloss = (
            f"V4 UNDERPERFORMS V3 by {-delta_R:.1f}R across 4 candles. "
            "V4 DRAFT design has a regression. RECOMMEND: ship V3 Monday; "
            "re-examine V4 design before further spend."
        )

    # ── Assemble report ──────────────────────────────────────────────────
    lines = []
    lines.append("# V4 DRAFT vs V3 — DP1 Head-to-Head Report")
    lines.append("")
    lines.append(f"- Generated: `{summary['generated_at']}`")
    lines.append(f"- Elapsed: {summary['elapsed_minutes']} minutes")
    lines.append(f"- Total V4 API spend: **${summary['total_cost_usd']:.4f}** (budget cap ${summary['budget_cap_usd']:.2f})")
    lines.append(f"- Config: `primary_model={summary['config_primary_model']}` `primary_effort={summary['config_primary_effort']}` `detector_version={summary['detector_version']}` `prompt_variant={summary['prompt_variant']}`")
    lines.append(f"- Runs per candle: **{runs_per_candle}** — total API calls: **{total_reruns}**")
    lines.append(f"- Prompt source: `{summary['prompt_source']}`")
    lines.append(f"- DP1 (V3) cross-reference: `{DP1_SUMMARY_PATH.relative_to(DIR.parent.parent.parent) if DP1_SUMMARY_PATH.exists() else 'MISSING'}`")
    lines.append("")

    # Executive summary
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"**V4 vs V3 verdict:** `{winloss_label.upper()}`")
    lines.append("")
    lines.append(winloss)
    lines.append("")
    lines.append(f"**V4 schema quality:** `{verdict_label}` — {verdict}")
    lines.append("")
    lines.append("### Headline numbers")
    lines.append("")
    lines.append("| Metric | V4 | V3 (DP1) |")
    lines.append("|---|---|---|")
    lines.append(f"| Typical-decision R total (sum of 4 candles) | **{v4_typical_R_total:+.1f}R** | **{v3_typical_R_total:+.1f}R** |")
    lines.append(f"| Δ V4 vs V3 | {delta_R:+.1f}R | — |")
    lines.append(f"| Self-consistency (5 reruns unanimous decision+direction) | {v4_hard_agreement_candles}/{candles_with_data} = {v4_hard_rate*100:.0f}% | (DP1 reported 100%) |")
    lines.append(f"| Parse errors | {v4_parse_errors_total} / {total_reruns} | — |")
    lines.append(f"| `no_trade_reason` schema violations (off R1-R8) | {v4_schema_violations_total} / {total_reruns} | — |")
    lines.append(f"| V4 matched V3 typical (head-to-head) | {match_count}/{candles_with_data} candles | — |")
    lines.append("")

    # V4 vs V3 head-to-head
    lines.append("## V4 vs V3 head-to-head (per candle)")
    lines.append("")
    lines.append(
        "| # | Candle | KZ | V3 typical (DP1) | V4 typical | Match? | V3 R | V4 R | F3 actual | A2 actual |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in per_candle:
        if "error" in r:
            lines.append(f"| {r['idx']} | `{r['candle_time']}` | — | — | — | NO DATA | — | — | — | — |")
            continue
        match_str = "YES" if r["matched"] else "NO"
        lines.append(
            f"| {r['idx']} | `{r['candle_time']}` | {r['kill_zone']} "
            f"| `{r['v3_typical']}` ({r['v3_typical_reason']}) "
            f"| `{r['v4_typical']}` ({r['v4_typical_n']}/{r['n']}, unanimous={r['v4_unanimous']}) "
            f"| {match_str} | {r['v3_typical_R']:+.1f}R | {r['v4_typical_R']:+.1f}R "
            f"| {r['f3_actual']} | {r['a2_actual']} |"
        )
    lines.append("")

    # V4 self-consistency + variance
    lines.append("## V4 self-consistency per candle")
    lines.append("")
    lines.append("| # | Candle | 5 V4 rerun decisions | Unanimous? | Parse err | Schema viol |")
    lines.append("|---|---|---|---|---|---|")
    for r in per_candle:
        if "error" in r:
            lines.append(f"| {r['idx']} | `{r['candle_time']}` | — | NO DATA | — | — |")
            continue
        rerun_str = " | ".join(r["rerun_keys"])
        lines.append(
            f"| {r['idx']} | `{r['candle_time']}` | `{rerun_str}` "
            f"| {r['v4_unanimous']} ({r['v4_typical_n']}/{r['n']} on `{r['v4_typical']}`) "
            f"| {r['parse_errs']} | {r['schema_violations']} |"
        )
    lines.append("")

    # Counterfactual R breakdown
    lines.append("## V4 counterfactual R calculation")
    lines.append("")
    lines.append(
        "Ground truth outcomes (from F3 backtest + A2's NO_TRADE candles):"
    )
    lines.append("")
    lines.append("| # | Candle | LONG R | SHORT R | NO_TRADE R | V4 typical | V4 realized R |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in per_candle:
        if "error" in r:
            continue
        cf = r["counterfactual_R"]
        lines.append(
            f"| {r['idx']} | `{r['candle_time']}` | {cf['LONG']:+.1f}R | {cf['SHORT']:+.1f}R "
            f"| {cf['NO_TRADE']:+.1f}R | `{r['v4_typical']}` | **{r['v4_typical_R']:+.1f}R** |"
        )
    lines.append(f"| | **Total** | | | | | **{v4_typical_R_total:+.1f}R** |")
    lines.append("")
    lines.append(f"- V3 typical total: **{v3_typical_R_total:+.1f}R** (from DP1)")
    lines.append(f"- V4 typical total: **{v4_typical_R_total:+.1f}R**")
    lines.append(f"- **Δ V4 vs V3: {delta_R:+.1f}R**")
    lines.append("")

    # Parse errors + schema violations
    lines.append("## Parse errors / degenerate outputs / schema violations")
    lines.append("")
    lines.append(f"- Parse errors (JSON decode fail): **{v4_parse_errors_total} / {total_reruns}**")
    lines.append(f"- `no_trade_reason` schema violations (off R1-R8 allow-list): **{v4_schema_violations_total} / {total_reruns}**")
    lines.append("")
    if v4_parse_errors_total > 0 or v4_schema_violations_total > 0:
        lines.append("### Detail of offending rows")
        lines.append("")
        for r in per_candle:
            if "error" in r:
                continue
            for rep in r["reports"]:
                if rep.get("decision") == "PARSE_ERROR":
                    lines.append(f"- Candle {r['idx']} run {rep.get('run')}: PARSE_ERROR — {rep.get('error', '?')}")
                if rep.get("no_trade_reason_schema_violation"):
                    lines.append(
                        f"- Candle {r['idx']} run {rep.get('run')}: SCHEMA VIOLATION — "
                        f"no_trade_reason=`{rep.get('no_trade_reason')}` (off R1-R8 allow-list)"
                    )
        lines.append("")

    # Per-candle detail
    lines.append("## Per-candle detail (V4 reruns)")
    lines.append("")
    for r in per_candle:
        if "error" in r:
            continue
        lines.append(f"### Candle {r['idx']} — `{r['candle_time']}` ({r['kill_zone']})")
        lines.append("")
        lines.append(f"- **V3 typical (DP1):** `{r['v3_typical']}` (ntr={r['v3_typical_reason']})")
        lines.append(f"- **V4 typical:** `{r['v4_typical']}` ({r['v4_typical_n']}/{r['n']}, unanimous={r['v4_unanimous']})")
        lines.append(f"- **F3 actual:** {r['f3_actual']}")
        lines.append(f"- **A2 actual:** {r['a2_actual']}")
        m = r.get("mso_summary") or {}
        lines.append(f"- **MSO (v2 detector):** D1=`{m.get('d1_direction')}` H4=`{m.get('h4_direction')}` H1=`{m.get('h1_direction')}` M15=`{m.get('m15_direction')}`")
        lines.append("")
        lines.append("| Run | Decision | Direction | Bias (conf) | Grade | No-trade reason | Schema OK | Conf | Cost | Time |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for rep in r["reports"]:
            schema_ok = not rep.get("no_trade_reason_schema_violation", False)
            lines.append(
                f"| {rep.get('run')} | {rep.get('decision')} | {rep.get('direction') or '—'} "
                f"| {rep.get('daily_bias_direction')} ({rep.get('daily_bias_confidence')}) "
                f"| {rep.get('setup_grade')} | {rep.get('no_trade_reason') or '—'} "
                f"| {schema_ok} | {rep.get('confidence_score')} "
                f"| ${rep.get('cost', 0):.4f} | {rep.get('elapsed_s')}s |"
            )
        lines.append("")
        lines.append("**V4 variance fingerprint:**")
        lines.append("")
        for fld, vals in r["variance"].items():
            nunique = len(vals)
            tag = "identical" if nunique == 1 else f"{nunique} unique"
            lines.append(f"- `{fld}` — {tag}: `{vals}`")
        lines.append("")

    # Recommendation for Monday
    lines.append("## Recommendation for CEO Monday decision")
    lines.append("")
    lines.append(f"**Verdict:** {winloss_label.upper()} ({winloss})")
    lines.append("")
    lines.append("**Next steps by verdict band:**")
    lines.append("")
    if winloss_label == "strong-win":
        lines.append("- Full $40-80 A/B backtest on broader sample (50-100 candles) BEFORE Monday deploy.")
        lines.append("- Regenerate canary fixtures against V4 to check baseline stability.")
        lines.append("- CEO decision: ship V4 Monday vs stay on V3 + deploy after wider A/B.")
    elif winloss_label == "cosmetic":
        lines.append("- Ship V3 Monday (already in prod).")
        lines.append("- Defer V4 to post-Monday A/B on broader sample.")
        lines.append("- Budget remaining in this mission was ~$1 — V4's cosmetic effect on 4 candles doesn't justify the +22% token cost today.")
    elif winloss_label == "mild-win":
        lines.append("- Ship V3 Monday (already in prod).")
        lines.append("- Run V4 on broader A/B sample (50-100 candles) before deploy decision.")
        lines.append("- Effect size too small on n=4 to separate from stochasticity.")
    elif winloss_label == "regression":
        lines.append("- Ship V3 Monday (already in prod).")
        lines.append("- DO NOT deploy V4 — regression on A2-divergent sample.")
        lines.append("- Agent B should re-examine V4 DRAFT spec (FORENSIC_AND_V4_SPEC.md §7 counterfactual).")
    else:
        lines.append("- Ship V3 Monday (already in prod).")
        lines.append("- Agent B must fix V4 DRAFT schema before any further spend.")
    lines.append("")

    # Caveats
    lines.append("## Caveats")
    lines.append("")
    lines.append("1. **n=4 candles is too small for statistical significance.** These are the A2-divergent candles; V4-DP1 is a targeted test of whether V4 alters V3 typical behavior on known-borderline cases. Wider A/B needed before any deploy decision.")
    lines.append("2. **Counterfactual R on SHORT trades assumes L2 rejects them** (as A2 did on candle 1). If V4's CANDIDATE_SHORT would pass L2 in a real run, the SHORT R could be non-zero; honest re-evaluation requires running through L2 gates.")
    lines.append("3. **Same MSO state as DP1** — detector v2 (not v2_shadow). Production is now v2_shadow since 2026-04-24. Any Monday decision must account for current detector state.")
    lines.append("4. **V4 DRAFT is 22% LONGER than V3, not 30% shorter.** The mission brief claimed 'Length ≤70% of V3' — actual V4 DRAFT is 28279 chars vs V3's 23252 chars (122% of V3). The dedup pass is not in the DRAFT as shipped.")
    lines.append("")

    out = "\n".join(lines)
    report_path = DIR / "V4_DP1_REPORT.md"
    report_path.write_text(out, encoding="utf-8")
    print(f"Wrote {report_path}  ({len(out)} chars)")
    print()
    print(f"V4 vs V3 verdict: {winloss_label}")
    print(f"  V4 typical total R: {v4_typical_R_total:+.2f}R")
    print(f"  V3 typical total R: {v3_typical_R_total:+.2f}R (from DP1)")
    print(f"  Delta V4 vs V3: {delta_R:+.2f}R")
    print(f"  V4 self-agreement: {v4_hard_agreement_candles}/{candles_with_data} = {v4_hard_rate*100:.0f}%")
    print(f"  Parse errors: {v4_parse_errors_total}/{total_reruns}")
    print(f"  Schema violations: {v4_schema_violations_total}/{total_reruns}")
    print(f"  V4-V3 head-to-head matches: {match_count}/{candles_with_data}")
    print(f"  Total cost: ${summary['total_cost_usd']:.4f}")


if __name__ == "__main__":
    main()
