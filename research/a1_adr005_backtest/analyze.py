#!/usr/bin/env python3
"""ADR-005 A1 backtest aggregator + pre-registered statistical test.

PRE-REGISTERED DISCRIMINATION CRITERIA (frozen before looking at data;
any post-hoc tweaking of these numbers would break the inference):

  AI DISCRIMINATES on touch if ALL hold:
    1. P(CAND | touch=0) >= 1.5 * P(CAND | touch>=2)
    2. Bonferroni-adjusted p < 0.05 (k = 3 FVG strata × 1 primary = 3 tests
       on the touch axis; conservative k=3)
    3. n >= 30 per arm (touch=0 arm AND touch>=2 arm).

  AI DISCRIMINATES on FVG if ALL hold:
    1. P(CAND | fvg_count>=3) >= 1.3 * P(CAND | fvg_count=0)
    2. Bonferroni-adjusted p < 0.05 (k = 4 touch strata × 1 primary = 4 tests
       on the FVG axis; conservative k=4)
    3. n >= 30 per arm.

ALL PROPORTION ESTIMATES USE WILSON 95% CIs. All two-proportion tests use
a normal approximation to the difference-of-proportions with pooled
standard error (equivalent to χ² of 2×2; same p-value).

Usage:
  python research/a1_adr005_backtest/analyze.py \
      --slice-dir research/a1_adr005_backtest/slices \
      --out-md research/a1_adr005_backtest/ANALYSIS.md

This script is content-addressed; its sha256 is logged to the ANALYSIS.md
header so post-hoc criterion tweaks are detectable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable


# ── PRE-REGISTERED THRESHOLDS (DO NOT TUNE AFTER DATA LOOK) ─────────────────

DISCRIMINATION_TOUCH_RATIO = 1.5          # touch=0 rate must be >= 1.5× touch>=2 rate
DISCRIMINATION_FVG_RATIO = 1.3            # fvg>=3 rate must be >= 1.3× fvg=0 rate
BONFERRONI_TOUCH_K = 3                    # k tests on touch axis
BONFERRONI_FVG_K = 4                      # k tests on FVG axis
ALPHA_RAW = 0.05
MIN_N_PER_ARM = 30


# ── Stats helpers ───────────────────────────────────────────────────────────

def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion.

    Reference: Wilson (1927). https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval

    Returns (lower, upper) in [0, 1]. For n=0, returns (0, 0).
    """
    if n <= 0:
        return (0.0, 0.0)
    p_hat = successes / n
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z * z / (4 * n)) / n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def two_prop_pvalue(a_successes: int, a_n: int, b_successes: int, b_n: int) -> float:
    """Two-proportion z-test p-value (two-sided), pooled SE.

    Same value as χ² test on a 2×2 table.

    Returns 1.0 when pooled p_hat is 0 or 1 (cannot reject null) or when
    either n=0.
    """
    if a_n <= 0 or b_n <= 0:
        return 1.0
    p_a = a_successes / a_n
    p_b = b_successes / b_n
    pooled = (a_successes + b_successes) / (a_n + b_n)
    if pooled <= 0 or pooled >= 1:
        return 1.0
    se = math.sqrt(pooled * (1 - pooled) * (1 / a_n + 1 / b_n))
    if se == 0:
        return 1.0
    z = (p_a - p_b) / se
    # Two-sided p = 2 * (1 - Phi(|z|)). Use standard normal via erf.
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return max(0.0, min(1.0, p))


# ── Data loading ────────────────────────────────────────────────────────────

def load_slice_rows(slice_dir: Path) -> list[dict]:
    rows = []
    for sub in sorted(slice_dir.iterdir()):
        if not sub.is_dir():
            continue
        log_path = sub / "candidate_features_log.jsonl"
        if not log_path.exists():
            continue
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:  # noqa: BLE001
                print(f"WARN: bad JSON in {log_path}: {e}", file=sys.stderr)
    return rows


# ── Row filters and stratification ──────────────────────────────────────────

def has_ai_decision(row: dict) -> bool:
    """Only rows where the AI was actually consulted (not pre-AI-gate skips)."""
    if row.get("pre_ai_gate_skipped"):
        return False
    dec = row.get("ai_decision") or row.get("decision")
    # Accept CANDIDATE + NO_TRADE. Exclude ERROR / PARSE_ERROR / None.
    return dec in ("CANDIDATE", "NO_TRADE")


def touch_stratum(touch: int | None) -> str:
    """Bucket h1_opp_ob_touch into {'missing', '0', '1', '2', '>=3'}."""
    if touch is None:
        return "missing"
    if touch < 0:
        return "missing"
    if touch == 0:
        return "0"
    if touch == 1:
        return "1"
    if touch == 2:
        return "2"
    return ">=3"


def fvg_stratum(total: int | None) -> str:
    """Bucket h1+m15 unfilled FVG total into {'0', '1-2', '>=3'}.

    Rationale: the ADR-005 brief frames this as "P(CAND | fvg=0) vs
    P(CAND | fvg>=3)" with an intermediate bucket; total = H1 + M15
    matches the additive feature-importance signal from Phase 1 Track A
    (h1_fvg + m15_fvg ranked #1/#2 for primary).
    """
    if total is None or total < 0:
        return "missing"
    if total == 0:
        return "0"
    if total <= 2:
        return "1-2"
    return ">=3"


def direction_stratum(d: str | None) -> str:
    if d in ("LONG", "SHORT"):
        return d
    return "UNCLEAR"


# ── Core aggregation ────────────────────────────────────────────────────────

def aggregate(rows: Iterable[dict]) -> dict:
    """Build per-stratum counts of (CAND, total) and overall per-axis counts."""
    full = defaultdict(lambda: {"cand": 0, "total": 0})       # (touch, fvg, dir)
    by_touch = defaultdict(lambda: {"cand": 0, "total": 0})    # touch alone
    by_fvg = defaultdict(lambda: {"cand": 0, "total": 0})      # fvg alone
    by_touch_dir = defaultdict(lambda: {"cand": 0, "total": 0})  # (touch, dir)
    by_fvg_dir = defaultdict(lambda: {"cand": 0, "total": 0})    # (fvg, dir)

    total_rows = 0
    ai_rows = 0
    for r in rows:
        total_rows += 1
        if not has_ai_decision(r):
            continue
        ai_rows += 1
        touch = r.get("h1_opp_ob_touch")
        if touch is None:
            touch = -1
        h1_fvg = r.get("h1_fvg_unfilled_count") or 0
        m15_fvg = r.get("m15_fvg_unfilled_count") or 0
        fvg_total = int(h1_fvg) + int(m15_fvg)
        direction = r.get("ai_direction_evaluated")

        t_key = touch_stratum(int(touch))
        f_key = fvg_stratum(fvg_total)
        d_key = direction_stratum(direction)

        is_cand = (r.get("ai_decision") or r.get("decision")) == "CANDIDATE"

        def bump(bucket):
            bucket["total"] += 1
            if is_cand:
                bucket["cand"] += 1

        bump(full[(t_key, f_key, d_key)])
        bump(by_touch[t_key])
        bump(by_fvg[f_key])
        bump(by_touch_dir[(t_key, d_key)])
        bump(by_fvg_dir[(f_key, d_key)])

    return {
        "n_total_rows": total_rows,
        "n_ai_rows": ai_rows,
        "by_touch": dict(by_touch),
        "by_fvg": dict(by_fvg),
        "by_touch_dir": {f"{t}|{d}": v for (t, d), v in by_touch_dir.items()},
        "by_fvg_dir": {f"{f}|{d}": v for (f, d), v in by_fvg_dir.items()},
        "full": {f"{t}|{f}|{d}": v for (t, f, d), v in full.items()},
    }


def fmt_prop(succ: int, n: int) -> str:
    if n == 0:
        return "n=0"
    p = succ / n * 100
    lo, hi = wilson_ci(succ, n)
    return f"{p:.1f}% [{lo*100:.1f}, {hi*100:.1f}] (n={n})"


# ── Discrimination verdict ──────────────────────────────────────────────────

def decide_touch(by_touch: dict) -> dict:
    t0 = by_touch.get("0", {"cand": 0, "total": 0})
    t2plus = {
        "cand": by_touch.get("2", {}).get("cand", 0) + by_touch.get(">=3", {}).get("cand", 0),
        "total": by_touch.get("2", {}).get("total", 0) + by_touch.get(">=3", {}).get("total", 0),
    }

    p0 = t0["cand"] / t0["total"] if t0["total"] else 0.0
    p2 = t2plus["cand"] / t2plus["total"] if t2plus["total"] else 0.0
    ratio = p0 / p2 if p2 > 0 else float("inf")

    raw_p = two_prop_pvalue(t0["cand"], t0["total"], t2plus["cand"], t2plus["total"])
    bonf_p = min(1.0, raw_p * BONFERRONI_TOUCH_K)

    criteria = {
        "ratio_ge_1.5": ratio >= DISCRIMINATION_TOUCH_RATIO,
        "bonf_p_lt_0.05": bonf_p < ALPHA_RAW,
        "n_touch0_ge_30": t0["total"] >= MIN_N_PER_ARM,
        "n_touch2plus_ge_30": t2plus["total"] >= MIN_N_PER_ARM,
    }
    verdict = all(criteria.values())

    return {
        "t0_cand": t0["cand"], "t0_n": t0["total"], "t0_p": p0,
        "t2plus_cand": t2plus["cand"], "t2plus_n": t2plus["total"], "t2plus_p": p2,
        "ratio": ratio,
        "raw_p": raw_p,
        "bonf_p": bonf_p,
        "criteria": criteria,
        "discriminates": verdict,
    }


def decide_fvg(by_fvg: dict) -> dict:
    f0 = by_fvg.get("0", {"cand": 0, "total": 0})
    f3plus = by_fvg.get(">=3", {"cand": 0, "total": 0})

    p0 = f0["cand"] / f0["total"] if f0["total"] else 0.0
    p3 = f3plus["cand"] / f3plus["total"] if f3plus["total"] else 0.0
    ratio = p3 / p0 if p0 > 0 else float("inf")

    raw_p = two_prop_pvalue(f0["cand"], f0["total"], f3plus["cand"], f3plus["total"])
    bonf_p = min(1.0, raw_p * BONFERRONI_FVG_K)

    criteria = {
        "ratio_ge_1.3": ratio >= DISCRIMINATION_FVG_RATIO,
        "bonf_p_lt_0.05": bonf_p < ALPHA_RAW,
        "n_fvg0_ge_30": f0["total"] >= MIN_N_PER_ARM,
        "n_fvg3plus_ge_30": f3plus["total"] >= MIN_N_PER_ARM,
    }
    verdict = all(criteria.values())

    return {
        "f0_cand": f0["cand"], "f0_n": f0["total"], "f0_p": p0,
        "f3plus_cand": f3plus["cand"], "f3plus_n": f3plus["total"], "f3plus_p": p3,
        "ratio": ratio,
        "raw_p": raw_p,
        "bonf_p": bonf_p,
        "criteria": criteria,
        "discriminates": verdict,
    }


# ── Markdown rendering ──────────────────────────────────────────────────────

def render_md(agg: dict, touch_verdict: dict, fvg_verdict: dict,
              script_hash: str, slice_dir: Path) -> str:
    lines: list[str] = []
    lines.append("# ADR-005 A1 backtest — statistical analysis")
    lines.append("")
    lines.append("**Question:** Does the GTOS production AI (Sonnet 4.6, effort=max) already")
    lines.append("discriminate on H1 opposing-OB touch_count + H1/M15 FVG unfilled counts?")
    lines.append("")
    lines.append(f"**Analysis script sha256:** `{script_hash}`")
    lines.append(f"**Slice dir:** `{slice_dir}`")
    lines.append("")
    lines.append("## Pre-registered criteria (frozen before data look)")
    lines.append("")
    lines.append("- **Touch:** P(CAND | touch=0) ≥ 1.5× P(CAND | touch≥2), Bonferroni p<0.05 (k=3), n≥30/arm.")
    lines.append("- **FVG:**   P(CAND | fvg≥3) ≥ 1.3× P(CAND | fvg=0),   Bonferroni p<0.05 (k=4), n≥30/arm.")
    lines.append("- All CIs are Wilson 95%. Two-proportion p-values are pooled z.")
    lines.append("")
    lines.append("## Data")
    lines.append("")
    lines.append(f"- Total rows logged across slices: **{agg['n_total_rows']}**")
    lines.append(f"- Rows with AI decision (post-prescreen, not pre-AI-gate-skipped): **{agg['n_ai_rows']}**")
    lines.append("")

    # Touch strata table
    lines.append("## Touch-count stratification (all AI-evaluated rows)")
    lines.append("")
    lines.append("| Touch | n | CAND | P(CAND) | Wilson 95% CI |")
    lines.append("|---:|---:|---:|---:|---|")
    for key in ("0", "1", "2", ">=3", "missing"):
        b = agg["by_touch"].get(key, {"cand": 0, "total": 0})
        if b["total"] == 0:
            lines.append(f"| {key} | 0 | 0 | n/a | n/a |")
        else:
            p = b["cand"] / b["total"] * 100
            lo, hi = wilson_ci(b["cand"], b["total"])
            lines.append(f"| {key} | {b['total']} | {b['cand']} | {p:.1f}% | [{lo*100:.1f}, {hi*100:.1f}] |")
    lines.append("")

    # FVG strata table
    lines.append("## FVG total (H1+M15) stratification (all AI-evaluated rows)")
    lines.append("")
    lines.append("| FVG total | n | CAND | P(CAND) | Wilson 95% CI |")
    lines.append("|---:|---:|---:|---:|---|")
    for key in ("0", "1-2", ">=3", "missing"):
        b = agg["by_fvg"].get(key, {"cand": 0, "total": 0})
        if b["total"] == 0:
            lines.append(f"| {key} | 0 | 0 | n/a | n/a |")
        else:
            p = b["cand"] / b["total"] * 100
            lo, hi = wilson_ci(b["cand"], b["total"])
            lines.append(f"| {key} | {b['total']} | {b['cand']} | {p:.1f}% | [{lo*100:.1f}, {hi*100:.1f}] |")
    lines.append("")

    # 2x2 touch × direction table
    lines.append("## Touch × Direction matrix (CAND / total per cell)")
    lines.append("")
    lines.append("| Touch | LONG | SHORT | UNCLEAR |")
    lines.append("|---:|---|---|---|")
    for t in ("0", "1", "2", ">=3", "missing"):
        row = [t]
        for d in ("LONG", "SHORT", "UNCLEAR"):
            b = agg["by_touch_dir"].get(f"{t}|{d}", {"cand": 0, "total": 0})
            row.append(f"{b['cand']}/{b['total']}" if b['total'] > 0 else "0/0")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # Touch verdict
    lines.append("## Touch discrimination verdict")
    lines.append("")
    lines.append(f"- P(CAND | touch=0) = {touch_verdict['t0_cand']}/{touch_verdict['t0_n']} = **{touch_verdict['t0_p']*100:.2f}%**")
    lines.append(f"  · Wilson 95% CI: [{wilson_ci(touch_verdict['t0_cand'], touch_verdict['t0_n'])[0]*100:.2f}, "
                 f"{wilson_ci(touch_verdict['t0_cand'], touch_verdict['t0_n'])[1]*100:.2f}]")
    lines.append(f"- P(CAND | touch≥2) = {touch_verdict['t2plus_cand']}/{touch_verdict['t2plus_n']} = **{touch_verdict['t2plus_p']*100:.2f}%**")
    lines.append(f"  · Wilson 95% CI: [{wilson_ci(touch_verdict['t2plus_cand'], touch_verdict['t2plus_n'])[0]*100:.2f}, "
                 f"{wilson_ci(touch_verdict['t2plus_cand'], touch_verdict['t2plus_n'])[1]*100:.2f}]")
    lines.append(f"- Ratio (touch=0 / touch≥2) = **{touch_verdict['ratio']:.2f}×** (pre-reg threshold 1.5×)")
    lines.append(f"- Two-proportion raw p = {touch_verdict['raw_p']:.4g}")
    lines.append(f"- Bonferroni-adjusted p (k={BONFERRONI_TOUCH_K}) = **{touch_verdict['bonf_p']:.4g}** (pre-reg threshold 0.05)")
    lines.append("")
    lines.append("### Criteria check")
    for k, v in touch_verdict["criteria"].items():
        mark = "PASS" if v else "FAIL"
        lines.append(f"- `{k}`: {mark}")
    lines.append("")
    if touch_verdict["discriminates"]:
        lines.append("**Touch verdict: AI DISCRIMINATES on h1_opp_ob_touch.**")
    else:
        lines.append("**Touch verdict: AI FAILS TO DISCRIMINATE on h1_opp_ob_touch.**")
    lines.append("")

    # FVG verdict
    lines.append("## FVG discrimination verdict")
    lines.append("")
    lines.append(f"- P(CAND | fvg=0) = {fvg_verdict['f0_cand']}/{fvg_verdict['f0_n']} = **{fvg_verdict['f0_p']*100:.2f}%**")
    lines.append(f"  · Wilson 95% CI: [{wilson_ci(fvg_verdict['f0_cand'], fvg_verdict['f0_n'])[0]*100:.2f}, "
                 f"{wilson_ci(fvg_verdict['f0_cand'], fvg_verdict['f0_n'])[1]*100:.2f}]")
    lines.append(f"- P(CAND | fvg≥3) = {fvg_verdict['f3plus_cand']}/{fvg_verdict['f3plus_n']} = **{fvg_verdict['f3plus_p']*100:.2f}%**")
    lines.append(f"  · Wilson 95% CI: [{wilson_ci(fvg_verdict['f3plus_cand'], fvg_verdict['f3plus_n'])[0]*100:.2f}, "
                 f"{wilson_ci(fvg_verdict['f3plus_cand'], fvg_verdict['f3plus_n'])[1]*100:.2f}]")
    lines.append(f"- Ratio (fvg≥3 / fvg=0) = **{fvg_verdict['ratio']:.2f}×** (pre-reg threshold 1.3×)")
    lines.append(f"- Two-proportion raw p = {fvg_verdict['raw_p']:.4g}")
    lines.append(f"- Bonferroni-adjusted p (k={BONFERRONI_FVG_K}) = **{fvg_verdict['bonf_p']:.4g}** (pre-reg threshold 0.05)")
    lines.append("")
    lines.append("### Criteria check")
    for k, v in fvg_verdict["criteria"].items():
        mark = "PASS" if v else "FAIL"
        lines.append(f"- `{k}`: {mark}")
    lines.append("")
    if fvg_verdict["discriminates"]:
        lines.append("**FVG verdict: AI DISCRIMINATES on FVG total.**")
    else:
        lines.append("**FVG verdict: AI FAILS TO DISCRIMINATE on FVG total.**")
    lines.append("")

    # Decision branch
    lines.append("## Decision branch")
    lines.append("")
    both = touch_verdict["discriminates"] and fvg_verdict["discriminates"]
    either = touch_verdict["discriminates"] or fvg_verdict["discriminates"]
    if both:
        lines.append("Both touch and FVG meet discrimination criteria → **close ADR-005 as 'no action needed'**.")
    elif not either:
        lines.append("Neither touch nor FVG meets discrimination criteria → **draft V4-A soft-bias prompt nudge**.")
    else:
        axis = "touch" if touch_verdict["discriminates"] else "FVG"
        other = "FVG" if touch_verdict["discriminates"] else "touch"
        lines.append(f"AI discriminates on {axis} but NOT on {other} → **partial action**: update ADR-005 to")
        lines.append(f"note partial discrimination, scope V4-A nudge to the {other} axis only.")
    lines.append("")
    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────

def compute_script_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slice-dir", required=True, type=Path,
                        help="Directory containing one sub-dir per slice, each with candidate_features_log.jsonl")
    parser.add_argument("--out-md", required=True, type=Path,
                        help="Markdown report output path.")
    parser.add_argument("--out-json", type=Path, default=None,
                        help="Optional JSON dump of aggregated counts + verdict.")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    script_hash = compute_script_hash(script_path)

    rows = load_slice_rows(args.slice_dir)
    agg = aggregate(rows)

    touch_verdict = decide_touch(agg["by_touch"])
    fvg_verdict = decide_fvg(agg["by_fvg"])

    md = render_md(agg, touch_verdict, fvg_verdict, script_hash, args.slice_dir)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    print(f"Wrote {args.out_md}")
    print(f"Script hash: {script_hash}")

    if args.out_json:
        args.out_json.write_text(json.dumps({
            "script_hash": script_hash,
            "agg": agg,
            "touch_verdict": touch_verdict,
            "fvg_verdict": fvg_verdict,
        }, indent=2, default=str), encoding="utf-8")
        print(f"Wrote {args.out_json}")


if __name__ == "__main__":
    main()
